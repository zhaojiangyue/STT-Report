from stt.pipeline import collect_targets


def test_collect_targets_batch_file(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("a.mp3\n#comment\nb.mp3\n", encoding="utf-8")
    targets = collect_targets([], str(f))
    assert targets == ["a.mp3", "b.mp3"]
