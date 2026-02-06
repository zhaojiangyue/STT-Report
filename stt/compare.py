import os
import time

from google import genai
from google.genai import types

from stt.downloaders.youtube import download_youtube_audio
from stt.utils import ensure_dir, safe_filename
from stt.core import generate_with_progress, get_existing_file


def summarize_media(client, model_id, media_file, title):
    prompt = (
        "Provide a concise summary (8-12 bullet points) of the audio content. "
        "Focus on key arguments, claims, and conclusions."
    )
    response = generate_with_progress(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=0.3),
        message=f"Summarizing {title}",
    )
    return response.text


def run_compare(a, b, *, config, lang, include_timestamps, with_transcript):
    output_root = config["paths"]["output_dir"]
    ensure_dir(output_root)
    if "youtube.com/" in a or "youtu.be/" in a:
        a = download_youtube_audio(a, output_root)
    if "youtube.com/" in b or "youtu.be/" in b:
        b = download_youtube_audio(b, output_root)

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=1800000),
    )
    model_id = config["models"]["text"]

    def upload(path):
        display_name = os.path.basename(path)
        myfile = get_existing_file(client, display_name)
        if not myfile:
            myfile = client.files.upload(file=path, config={"display_name": display_name})
        while True:
            myfile = client.files.get(name=myfile.name)
            if myfile.state.name == "ACTIVE":
                return myfile
            if myfile.state.name == "FAILED":
                raise RuntimeError("Processing failed.")
            time.sleep(5)

    file_a = upload(a)
    file_b = upload(b)

    summary_a = summarize_media(client, model_id, file_a, os.path.basename(a))
    summary_b = summarize_media(client, model_id, file_b, os.path.basename(b))

    compare_prompt = (
        "Compare these two summaries. Highlight similarities, differences, and key contrasts. "
        "Output Markdown with sections: # Similarities, # Differences, # Key Takeaways."
    )
    response = generate_with_progress(
        client,
        model_id,
        contents=[compare_prompt, f"Summary A:\n{summary_a}", f"Summary B:\n{summary_b}"],
        config=types.GenerateContentConfig(temperature=0.3),
        message="Generating Comparison Report",
    )

    base = f"{safe_filename(os.path.splitext(os.path.basename(a))[0])}_vs_{safe_filename(os.path.splitext(os.path.basename(b))[0])}"
    output_dir = os.path.join(output_root, f"{base}_comparison")
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, "comparison_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Comparison report saved: {out_path}")
