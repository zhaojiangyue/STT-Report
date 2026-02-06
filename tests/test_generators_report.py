from stt.generators import report


def test_build_prompt_basic():
    template = "Lang: {language}\n{headings}\n{timestamps_block}"
    text = report.build_prompt(template, "professional", "en", True)
    assert "English" in text
    assert "# What Is This?" in text
    assert "Key Points with Timestamps" in text


def test_transcript_prompt():
    p = report.transcript_prompt()
    assert "verbatim" in p.lower()
