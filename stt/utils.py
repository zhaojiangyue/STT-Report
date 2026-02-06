import json
import os
import re
import subprocess


def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "", name)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_audio_duration_seconds(path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def estimate_tokens(duration_seconds, tokens_per_minute):
    if duration_seconds is None:
        return None
    return int((duration_seconds / 60.0) * tokens_per_minute)
