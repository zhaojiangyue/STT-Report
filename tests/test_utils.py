import json
from stt import utils


def test_safe_filename():
    assert utils.safe_filename('a<>:"/\\|?*b') == "ab"


def test_json_roundtrip(tmp_path):
    path = tmp_path / "x.json"
    data = {"a": 1}
    utils.write_json(str(path), data)
    read = utils.read_json(str(path))
    assert read == data


def test_estimate_tokens():
    tokens = utils.estimate_tokens(120, 1500)
    assert tokens == 3000
