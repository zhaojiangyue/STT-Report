from stt.exporters import markdown


def test_export_markdown(tmp_path):
    path = tmp_path / "out.md"
    markdown.export_markdown("hello", str(path))
    assert path.read_text(encoding="utf-8") == "hello"
