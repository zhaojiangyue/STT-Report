import os

from stt.config import deep_merge, load_config, resolve_prompt, DEFAULT_CONFIG


def test_deep_merge_basic():
    base = {"a": 1, "b": {"c": 2}}
    override = {"b": {"d": 3}}
    merged = deep_merge(base, override)
    assert merged["a"] == 1
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 3


def test_load_config_missing(tmp_path):
    path = tmp_path / "missing.yaml"
    cfg = load_config(str(path))
    assert cfg["defaults"]["language"] == DEFAULT_CONFIG["defaults"]["language"]


def test_resolve_prompt_inline(tmp_path):
    prompt = "Hello {language}"
    resolved = resolve_prompt(prompt, str(tmp_path))
    assert resolved == prompt


def test_resolve_prompt_file(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text("PROMPT", encoding="utf-8")
    resolved = resolve_prompt({"file": str(p)}, str(tmp_path))
    assert resolved == "PROMPT"
