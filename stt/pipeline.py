import os

from stt.core import analyze_audio
from stt.downloaders.youtube import download_youtube_audio
from stt.utils import ensure_dir


def collect_targets(inputs, batch):
    targets = []
    if inputs:
        targets.extend(inputs)
    if batch:
        if os.path.isfile(batch):
            with open(batch, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    targets.append(line)
        elif os.path.isdir(batch):
            for name in os.listdir(batch):
                if name.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")):
                    targets.append(os.path.join(batch, name))
        else:
            print(f"Batch path not found: {batch}")
    return targets


def process_target(
    target,
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
    output_root = config["paths"]["output_dir"]
    ensure_dir(output_root)
    if "youtube.com/" in target or "youtu.be/" in target:
        target_file = download_youtube_audio(target, output_root)
    else:
        target_file = target

    analyze_audio(
        target_file,
        config=config,
        lang=lang,
        include_timestamps=include_timestamps,
        with_transcript=with_transcript,
        report_keys=report_keys,
        tts_enabled=tts_enabled,
        export_formats=export_formats,
        dry_run=dry_run,
    )
