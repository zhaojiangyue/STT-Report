import os


DEFAULT_CONFIG = {
    "defaults": {
        "language": "zh",
        "reports": ["professional", "children"],
        "tts": True,
        "timestamps": False,
        "export_formats": ["md"],
    },
    "models": {
        "text": "gemini-3-pro-preview",
        "audio": "gemini-2.5-flash-preview-tts",
    },
    "cost": {
        "tokens_per_minute": 1500,
        "usd_per_1k_tokens": 0.01,
    },
    "reports": {
        "professional": {
            "temperature": 0.3,
            "prompt": {"file": "prompts/professional.md"},
        },
        "children": {
            "temperature": 0.5,
            "prompt": {"file": "prompts/children.md"},
        },
    },
    "plugins": {
        "enabled": [],
        "config": {},
    },
    "paths": {
        "output_dir": "output",
        "prompts_dir": "prompts",
    },
    "intelligence": {
        "enabled": True,
        "auto_select_reports": True,
        "content_type_map": {
            "lecture": ["professional", "children"],
            "interview": ["professional"],
            "news": ["professional"],
            "tutorial": ["professional", "children"],
            "podcast": ["professional"],
            "meeting": ["professional"],
            "other": ["professional"],
        },
        "content_type_detection": True,
        "key_quotes": True,
        "fact_check": True,
        "follow_up_questions": True,
        "related_content": True,
        "knowledge_graph": True,
    },
}


def deep_merge(base, override):
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path):
    if os.path.exists(path):
        try:
            import yaml
        except ImportError:
            print("Warning: PyYAML not installed. Using defaults. Install with 'pip install pyyaml'.")
            return DEFAULT_CONFIG
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return deep_merge(DEFAULT_CONFIG, data)
    return DEFAULT_CONFIG


def resolve_prompt(prompt_spec, base_dir):
    if isinstance(prompt_spec, dict) and "file" in prompt_spec:
        path = prompt_spec["file"]
        if not os.path.isabs(path):
            path = os.path.join(base_dir, path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    if isinstance(prompt_spec, str):
        if prompt_spec.strip().endswith(".md") and os.path.exists(prompt_spec):
            with open(prompt_spec, "r", encoding="utf-8") as f:
                return f.read()
        return prompt_spec
    return ""
