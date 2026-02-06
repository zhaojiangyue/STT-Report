import os
import time

from stt.pipeline import process_target


def run_watch(watch_path, *, config, lang, include_timestamps, with_transcript, interval=5):
    if not os.path.isdir(watch_path):
        print(f"Watch path is not a directory: {watch_path}")
        return
    seen = set()
    print(f"Watching {watch_path} for new audio files...")
    while True:
        for name in os.listdir(watch_path):
            if not name.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")):
                continue
            full_path = os.path.join(watch_path, name)
            if full_path in seen:
                continue
            seen.add(full_path)
            print(f"New file detected: {full_path}")
            process_target(
                full_path,
                config=config,
                lang=lang,
                include_timestamps=include_timestamps,
                with_transcript=with_transcript,
                report_keys=None,
                tts_enabled=config["defaults"].get("tts", True),
                export_formats=config["defaults"].get("export_formats", ["md"]),
                dry_run=False,
            )
        time.sleep(interval)
