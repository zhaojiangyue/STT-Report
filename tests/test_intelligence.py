from stt.generators import intelligence


class DummyResp:
    def __init__(self, text):
        self.text = text


def dummy_generator(*args, **kwargs):
    return DummyResp("ok")


def test_detect_content_type():
    text = intelligence.detect_content_type(None, None, dummy_generator, None)
    assert text == "ok"


def test_follow_up_questions():
    text = intelligence.follow_up_questions(None, None, dummy_generator, None, "en")
    assert text == "ok"
