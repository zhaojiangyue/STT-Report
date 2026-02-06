def run_interactive(config):
    print("Interactive Report Builder")
    print("Select report types (comma-separated). Available:", ", ".join(config["reports"].keys()))
    reports_in = input("Reports [professional,children]: ").strip()
    if reports_in:
        reports = [x.strip() for x in reports_in.split(",") if x.strip()]
    else:
        reports = config["defaults"].get("reports", ["professional", "children"])

    lang = input("Target language (zh/en/ja) [zh]: ").strip() or config["defaults"].get("language", "zh")
    timestamps = input("Include timestamps? (y/n) [n]: ").strip().lower() == "y"
    export_formats = input("Export formats (md,pdf,docx,notion) [md]: ").strip()
    if export_formats:
        export_formats = [x.strip() for x in export_formats.split(",") if x.strip()]
    else:
        export_formats = config["defaults"].get("export_formats", ["md"])
    custom_prompt = None
    if input("Add custom prompt? (y/n) [n]: ").strip().lower() == "y":
        custom_prompt = input("Custom instruction: ").strip()

    return {
        "reports": reports,
        "lang": lang,
        "timestamps": timestamps,
        "export_formats": export_formats,
        "custom_prompt": custom_prompt,
    }
