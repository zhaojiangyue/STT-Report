import os
import subprocess
from stt.utils import safe_filename


def download_youtube_audio(url, output_dir):
    print("Detecting YouTube URL. Downloading audio...")
    cmd_get_title = ["yt-dlp", "--no-warnings", "--get-title", url]
    title = subprocess.check_output(cmd_get_title, text=True).strip()
    safe_title = safe_filename(title)
    mp3_filename = f"{safe_title}.mp3"
    output_folder_path = os.path.join(output_dir, f"{safe_title}_results", mp3_filename)

    if os.path.exists(mp3_filename):
        print(f"Audio already downloaded: {mp3_filename}")
        return mp3_filename
    if os.path.exists(output_folder_path):
        print(f"Audio found in output folder: {output_folder_path}")
        return output_folder_path

    cmd_download = [
        "yt-dlp",
        "--no-warnings",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        f"{safe_title}.%(ext)s",
        url,
    ]
    subprocess.run(cmd_download, check=True)
    print(f"Downloaded: {mp3_filename}")
    return mp3_filename
