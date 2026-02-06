import os
import subprocess

from stt.downloaders.youtube import download_youtube_audio


def test_download_youtube_audio_uses_safe_title(tmp_path, monkeypatch):
    def fake_check_output(cmd, text=True):
        return 'Bad:Title'

    def fake_run(cmd, check=True):
        # Ensure output template is sanitized
        assert any("BadTitle" in part for part in cmd)
        return 0

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(subprocess, "run", fake_run)

    output_dir = str(tmp_path)
    mp3 = download_youtube_audio("https://youtu.be/xyz", output_dir)
    assert mp3 == "BadTitle.mp3"
