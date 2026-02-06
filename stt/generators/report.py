from google.genai import types

LANGUAGE_MAP = {
    "zh": "Chinese (Mandarin)",
    "en": "English",
    "ja": "Japanese",
}

HEADINGS = {
    "zh": {
        "professional": ["这是什么？（简单解释）", "要点总结", "为什么重要？"],
        "children": ["小朋友版总结", "重点", "为什么有趣/重要"],
    },
    "en": {
        "professional": ["What Is This? (Simple Explanation)", "Key Points", "Why It Matters"],
        "children": ["Kids Version Summary", "Key Points", "Why It's Cool/Important"],
    },
    "ja": {
        "professional": ["これは何？（やさしい説明）", "要点まとめ", "なぜ重要？"],
        "children": ["こども向けまとめ", "ポイント", "なぜ面白い/大事？"],
    },
}

TIMESTAMP_BLOCK = {
    "zh": "## 关键要点（带时间戳）\n- 使用 [MM:SS] 格式，尽量准确。\n",
    "en": "## Key Points with Timestamps\n- Use [MM:SS] format and be as accurate as possible.\n",
    "ja": "## タイムスタンプ付き要点\n- [MM:SS] 形式で、できるだけ正確に。\n",
}


def get_headings(lang, report_key):
    lang_map = HEADINGS.get(lang, HEADINGS["en"])
    headings = lang_map.get(report_key, HEADINGS["en"][report_key])
    return "\n".join([f"# {h}" for h in headings])


def build_prompt(prompt_template, report_key, lang, include_timestamps):
    language_name = LANGUAGE_MAP.get(lang, "English")
    headings = get_headings(lang, report_key)
    timestamps_block = TIMESTAMP_BLOCK.get(lang, TIMESTAMP_BLOCK["en"]) if include_timestamps else ""
    return prompt_template.format(
        language=language_name,
        headings=headings,
        timestamps_block=timestamps_block,
    )


def transcript_prompt():
    return (
        "Objective: Provide a verbatim, word-for-word transcript of the audio content.\n"
        "Do not summarize. Do not leave out details. Capture every spoken word as accurately as possible.\n"
        "Output Format: Markdown document titled '# Verbatim Transcript'.\n"
    )


def generate_transcript(client, model_id, media_file, generator, output_path):
    response = generator(
        client,
        model_id,
        contents=[media_file, transcript_prompt()],
        config=types.GenerateContentConfig(temperature=0.1),
        message="Generating Verbatim Transcript",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    return response.text


def generate_report(
    client,
    model_id,
    media_file,
    generator,
    prompt_template,
    report_key,
    lang,
    include_timestamps,
    temperature,
    output_path,
):
    prompt = build_prompt(prompt_template, report_key, lang, include_timestamps)
    response = generator(
        client,
        model_id,
        contents=[media_file, prompt],
        config=types.GenerateContentConfig(temperature=temperature),
        message=f"Generating {report_key.title()} Report",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    return response.text
