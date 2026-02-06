def export_markdown(content, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
