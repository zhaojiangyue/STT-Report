import os
import time
import threading
import json

from google import genai
from google.genai import types
from tqdm import tqdm

from stt.config import resolve_prompt
from stt.utils import ensure_dir, read_json, write_json, safe_filename, get_audio_duration_seconds, estimate_tokens
from stt.generators.report import generate_transcript, generate_report, LANGUAGE_MAP
from stt.generators.audio import text_to_speech
from stt.generators import intelligence
from stt.exporters import pdf as pdf_exporter
from stt.exporters import docx as docx_exporter
from stt.plugins.base import load_plugins


def generate_with_retry(client, model, contents, config, max_retries=5):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["disconnect", "timeout", "reset", "connection"]):
                wait_time = 10 * (attempt + 1)
                print(f"   Warning: Attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise


def show_progress(message, stop_event):
    spinners = ["|", "/", "-", "\\"]
    i = 0
    while not stop_event.is_set():
        print(f"\r{spinners[i % len(spinners)]} {message}...", end="", flush=True)
        time.sleep(0.2)
        i += 1
    print("\r" + " " * (len(message) + 10), end="\r")


def generate_with_progress(client, model, contents, config, message, max_retries=5):
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_progress, args=(message, stop_event))
    spinner_thread.start()
    try:
        return generate_with_retry(client, model, contents, config, max_retries)
    finally:
        stop_event.set()
        spinner_thread.join()


def get_existing_file(client, filename):
    print("Checking cloud cache...", end="")
    try:
        for file in client.files.list():
            if file.display_name == filename:
                if file.state.name == "ACTIVE":
                    print(" Found active cache! (Skipping upload)")
                    return file
                if file.state.name == "FAILED":
                    print(" Found corrupted file, deleting and re-uploading.")
                    client.files.delete(name=file.name)
                    return None
        print(" No cache found, preparing to upload.")
        return None
    except Exception:
        print(" (Cache check failed, proceeding to upload)")
        return None


def estimate_cost(path, config):
    duration = get_audio_duration_seconds(path)
    tokens = estimate_tokens(duration, config["cost"]["tokens_per_minute"])
    if tokens is None:
        return {"duration_seconds": None, "tokens": None, "usd": None}
    usd = (tokens / 1000.0) * config["cost"]["usd_per_1k_tokens"]
    return {"duration_seconds": duration, "tokens": tokens, "usd": usd}


def analyze_audio(
    audio_path,
    *,
    config,
    lang,
    include_timestamps,
    with_transcript,
    report_keys,
    tts_enabled,
    export_formats,
    dry_run,
):
    if not os.path.exists(audio_path):
        print(f"Error: File '{audio_path}' not found.")
        return

    if dry_run:
        estimate = estimate_cost(audio_path, config)
        print("Dry run cost estimate:")
        print(f"  Duration (sec): {estimate['duration_seconds']}")
        print(f"  Tokens: {estimate['tokens']}")
        print(f"  Estimated USD: {estimate['usd']}")
        return

    display_name = os.path.basename(audio_path)
    base_filename = os.path.splitext(display_name)[0]
    output_root = config["paths"]["output_dir"]
    output_dir = os.path.join(output_root, f"{safe_filename(base_filename)}_results")
    ensure_dir(output_dir)

    source_in_folder = os.path.join(output_dir, display_name)
    if not os.path.exists(source_in_folder) and os.path.exists(audio_path):
        os.replace(audio_path, source_in_folder)
        print(f"Moved source audio to: {source_in_folder}")

    checkpoint_path = os.path.join(output_dir, "checkpoint.json")
    checkpoint = read_json(checkpoint_path, default={})

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=1800000),
    )

    model_id = config["models"]["text"]
    audio_model_id = config["models"]["audio"]

    myfile = checkpoint.get("uploaded_file_name")
    if myfile:
        try:
            myfile = client.files.get(name=myfile)
        except Exception:
            myfile = None

    if not myfile:
        myfile = get_existing_file(client, display_name)
        if not myfile:
            print(f"Uploading: {source_in_folder} ...")
            max_upload_retries = 3
            for attempt in range(max_upload_retries):
                try:
                    start_upload = time.time()
                    myfile = client.files.upload(file=source_in_folder, config={"display_name": display_name})
                    upload_elapsed = int(time.time() - start_upload)
                    print(f"Upload successful: {myfile.name}")
                    print(f"Upload time: {upload_elapsed}s")
                    checkpoint["uploaded_file_name"] = myfile.name
                    write_json(checkpoint_path, checkpoint)
                    break
                except Exception as e:
                    print(f"   Warning: Upload attempt {attempt+1} failed: {e}")
                    if attempt == max_upload_retries - 1:
                        print(f"Upload failed permanently after {max_upload_retries} attempts.")
                        return
                    time.sleep(5)

    print("Waiting for Google to process audio...")
    processing_start = time.time()
    processing_timeout = config.get("timeouts", {}).get("processing_seconds", 1200)
    reupload_on_fail = config.get("timeouts", {}).get("reupload_on_fail", True)
    with tqdm(total=100, bar_format="{desc}: {bar} {elapsed}", desc="Processing") as pbar:
        while True:
            myfile = client.files.get(name=myfile.name)
            if myfile.state.name == "ACTIVE":
                pbar.update(100 - pbar.n)
                break
            if myfile.state.name == "FAILED":
                print("\nProcessing failed.")
                if reupload_on_fail:
                    print("Deleting failed file and re-uploading once...")
                    try:
                        client.files.delete(name=myfile.name)
                    except Exception:
                        pass
                    checkpoint.pop("uploaded_file_name", None)
                    write_json(checkpoint_path, checkpoint)
                    return analyze_audio(
                        audio_path,
                        config=config,
                        lang=lang,
                        include_timestamps=include_timestamps,
                        with_transcript=with_transcript,
                        report_keys=report_keys,
                        tts_enabled=tts_enabled,
                        export_formats=export_formats,
                        dry_run=dry_run,
                    )
                return
            elapsed = time.time() - processing_start
            if elapsed > processing_timeout:
                print(f"\nProcessing timeout after {int(elapsed)}s.")
                return
            if pbar.n < 90:
                pbar.update(5)
            time.sleep(5)

    plugins = load_plugins(config["plugins"].get("enabled", []), config["plugins"].get("config", {}))
    context = {"title": base_filename, "output_dir": output_dir}
    for plugin in plugins:
        plugin.on_start(context)

    prompts_dir = config["paths"]["prompts_dir"]
    report_texts = {}
    content_type_json = None
    content_type_value = None

    if config["intelligence"].get("enabled", True) and config["intelligence"].get("content_type_detection", True):
        if config["intelligence"].get("auto_select_reports", False) or report_keys is None:
            content_type_json = intelligence.detect_content_type(client, model_id, generate_with_progress, myfile)
            try:
                parsed = json.loads(content_type_json)
                content_type_value = parsed.get("type")
            except Exception:
                content_type_value = None
            if config["intelligence"].get("auto_select_reports", False) and report_keys is None:
                report_keys = config["intelligence"].get("content_type_map", {}).get(
                    content_type_value, config["defaults"].get("reports", ["professional", "children"])
                )

    if report_keys is None:
        report_keys = config["defaults"].get("reports", ["professional", "children"])

    if with_transcript and not checkpoint.get("transcript_done"):
        transcript_path = os.path.join(output_dir, f"{base_filename}_transcript.md")
        if not os.path.exists(transcript_path):
            generate_transcript(client, model_id, myfile, generate_with_progress, transcript_path)
        checkpoint["transcript_done"] = True
        write_json(checkpoint_path, checkpoint)

    for report_key in report_keys:
        report_path = os.path.join(output_dir, f"{base_filename}_{report_key}_{lang}_report.md")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_texts[report_key] = f.read()
            continue

        report_cfg = config["reports"].get(report_key)
        if not report_cfg:
            continue
        template = resolve_prompt(report_cfg.get("prompt"), prompts_dir)
        text = generate_report(
            client,
            model_id,
            myfile,
            generate_with_progress,
            template,
            report_key,
            lang,
            include_timestamps,
            report_cfg.get("temperature", 0.3),
            report_path,
        )
        report_texts[report_key] = text
        for plugin in plugins:
            plugin.on_report(context, report_key, report_path)

    if "children" in report_texts and tts_enabled and not checkpoint.get("tts_done"):
        audio_file = os.path.join(output_dir, f"{base_filename}_children_{lang}_audio.mp3")
        if not os.path.exists(audio_file):
            language_name = LANGUAGE_MAP.get(lang, "English")
            text_to_speech(client, audio_model_id, report_texts["children"], audio_file, language_name)
        checkpoint["tts_done"] = True
        write_json(checkpoint_path, checkpoint)

    if config["intelligence"].get("enabled", True) and not checkpoint.get("intelligence_done"):
        if config["intelligence"].get("content_type_detection", True):
            if content_type_json is None:
                content_type_json = intelligence.detect_content_type(client, model_id, generate_with_progress, myfile)
            with open(os.path.join(output_dir, "content_type.json"), "w", encoding="utf-8") as f:
                f.write(content_type_json)
        if config["intelligence"].get("key_quotes", True):
            quotes = intelligence.extract_key_quotes(client, model_id, generate_with_progress, myfile, lang)
            with open(os.path.join(output_dir, "key_quotes.md"), "w", encoding="utf-8") as f:
                f.write(quotes)
        if config["intelligence"].get("fact_check", True):
            flags = intelligence.fact_check_flags(client, model_id, generate_with_progress, myfile, lang)
            with open(os.path.join(output_dir, "fact_check.md"), "w", encoding="utf-8") as f:
                f.write(flags)
        if config["intelligence"].get("follow_up_questions", True):
            questions = intelligence.follow_up_questions(client, model_id, generate_with_progress, myfile, lang)
            with open(os.path.join(output_dir, "follow_up_questions.md"), "w", encoding="utf-8") as f:
                f.write(questions)
        if config["intelligence"].get("related_content", True):
            history_index = read_json(os.path.join(output_root, "index.json"), default={"items": []})
            titles = [i.get("title", "") for i in history_index.get("items", [])]
            related = intelligence.related_content(client, model_id, generate_with_progress, myfile, lang, titles)
            with open(os.path.join(output_dir, "related_content.md"), "w", encoding="utf-8") as f:
                f.write(related)
        if config["intelligence"].get("knowledge_graph", True):
            entities_json = intelligence.extract_entities(client, model_id, generate_with_progress, myfile)
            with open(os.path.join(output_dir, "entities.json"), "w", encoding="utf-8") as f:
                f.write(entities_json)
            try:
                data = json.loads(entities_json)
                entities = data.get("entities", [])
                topics = data.get("topics", [])
                graph_path = os.path.join(output_root, "knowledge_graph.json")
                intelligence.update_knowledge_graph(graph_path, base_filename, base_filename, entities, topics)
            except Exception:
                pass
        checkpoint["intelligence_done"] = True
        write_json(checkpoint_path, checkpoint)

    if export_formats:
        primary_text = report_texts.get("professional") or next(iter(report_texts.values()), "")
        if "pdf" in export_formats:
            pdf_exporter.export_pdf(primary_text, os.path.join(output_dir, f"{base_filename}.pdf"))
        if "docx" in export_formats:
            docx_exporter.export_docx(primary_text, os.path.join(output_dir, f"{base_filename}.docx"))
        if "notion" in export_formats:
            from stt.exporters.notion import export_notion
            export_notion(primary_text, config.get("notion", {}))

    index_path = os.path.join(output_root, "index.json")
    index = read_json(index_path, default={"items": []})
    index["items"].append({"title": base_filename, "path": output_dir})
    write_json(index_path, index)

    context["primary_report_text"] = report_texts.get("professional") or next(iter(report_texts.values()), "")
    for plugin in plugins:
        plugin.on_complete(context)

    print("\n" + "=" * 30)
    print(f"SUCCESS: All files located in '{output_dir}/'")
    print("=" * 30)
