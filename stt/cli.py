import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from stt.config import load_config
from stt.pipeline import collect_targets, process_target
from stt.downloaders.podcast import process_feeds
from stt import interactive
from stt import compare as compare_mode
from stt import server
from stt import watch as watch_mode




def main():
    import argparse

    parser = argparse.ArgumentParser(description="YouTube/Audio to Reports")
    parser.add_argument("inputs", nargs="*", help="Audio file(s) or YouTube URL(s)")
    parser.add_argument("--with-transcript", action="store_true", help="Generate verbatim transcript")
    parser.add_argument("--lang", choices=["zh", "en", "ja"], help="Report language")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--batch", help="Text file with URLs/paths or a folder path")
    parser.add_argument("--timestamps", action="store_true", help="Add timestamps in reports")
    parser.add_argument("--reports", help="Comma-separated report types (override config)")
    parser.add_argument("--format", help="Comma-separated export formats: md,pdf,docx,notion")
    parser.add_argument("--dry-run", action="store_true", help="Estimate cost and exit")
    parser.add_argument("--interactive", action="store_true", help="Interactive report builder")
    parser.add_argument("--compare", action="store_true", help="Comparison mode for two inputs")
    parser.add_argument("--serve", action="store_true", help="Run web UI dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Web UI port")
    parser.add_argument("--watch", help="Watch a folder for new audio files")
    parser.add_argument("--feeds", default="feeds.yaml", help="Podcast feeds config")

    args = parser.parse_args()
    config = load_config(args.config)
    lang = args.lang or config["defaults"].get("language", "zh")
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set. Please set it in .env or environment.")
        return

    if args.serve:
        server.run_server(config, args.port)
        return

    if args.watch:
        watch_mode.run_watch(
            args.watch,
            config=config,
            lang=lang,
            include_timestamps=args.timestamps or config["defaults"].get("timestamps", False),
            with_transcript=args.with_transcript,
        )
        return

    if args.interactive:
        selection = interactive.run_interactive(config)
        lang = selection["lang"]
        report_keys = selection["reports"]
        include_timestamps = selection["timestamps"]
        custom_prompt = selection.get("custom_prompt")
        if custom_prompt:
            config["reports"]["custom"] = {"temperature": 0.3, "prompt": custom_prompt}
            report_keys.append("custom")
        export_formats = selection["export_formats"]
    else:
        report_keys = None
        include_timestamps = args.timestamps or config["defaults"].get("timestamps", False)
        export_formats = (
            [x.strip() for x in args.format.split(",") if x.strip()]
            if args.format
            else config["defaults"].get("export_formats", ["md"])
        )

    if args.reports:
        report_keys = [x.strip() for x in args.reports.split(",") if x.strip()]

    tts_enabled = bool(config["defaults"].get("tts", True))

    if args.compare:
        if len(args.inputs) < 2:
            print("Comparison mode requires two inputs.")
            return
        compare_mode.run_compare(
            args.inputs[0],
            args.inputs[1],
            config=config,
            lang=lang,
            include_timestamps=include_timestamps,
            with_transcript=args.with_transcript,
        )
        return

    targets = collect_targets(args.inputs, args.batch)
    feeds_targets = process_feeds(args.feeds, config["paths"]["output_dir"])
    targets.extend(feeds_targets)

    if not targets:
        parser.print_help()
        print("\nExamples:")
        print("  python stt.py audio.mp3")
        print("  python stt.py https://youtu.be/xxx")
        print("  python stt.py https://youtu.be/xxx --with-transcript")
        print("  python stt.py --batch playlist.txt")
        print("  python stt.py --watch ./incoming")
        print("  python stt.py --serve --port 8080")
        return

    for target in targets:
        process_target(
            target,
            config=config,
            lang=lang,
            include_timestamps=include_timestamps,
            with_transcript=args.with_transcript,
            report_keys=report_keys,
            tts_enabled=tts_enabled,
            export_formats=export_formats,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
