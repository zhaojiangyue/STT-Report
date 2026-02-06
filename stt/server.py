import os
import threading

from stt.pipeline import process_target
from stt.utils import ensure_dir


def run_server(config, port):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask not installed. Install with 'pip install flask' to use --serve.")
        return

    app = Flask(__name__)
    jobs = {}

    @app.route("/", methods=["GET"])
    def index():
        return """
        <html>
          <head><title>STT-Report Dashboard</title></head>
          <body style="font-family: sans-serif; max-width: 720px; margin: 40px auto;">
            <h2>STT-Report Dashboard</h2>
            <form method="post" action="/process" enctype="multipart/form-data">
              <label>YouTube URL:</label><br/>
              <input type="text" name="url" style="width: 100%;"/><br/><br/>
              <label>Or upload audio file:</label><br/>
              <input type="file" name="file"/><br/><br/>
              <label>Language:</label>
              <select name="lang">
                <option value="zh">Chinese</option>
                <option value="en">English</option>
                <option value="ja">Japanese</option>
              </select><br/><br/>
              <label>Report Types (comma-separated):</label><br/>
              <input type="text" name="reports" style="width: 100%;" placeholder="professional,children"/><br/><br/>
              <label>Export Formats (comma-separated):</label><br/>
              <input type="text" name="formats" style="width: 100%;" placeholder="md,pdf,docx,notion"/><br/><br/>
              <label><input type="checkbox" name="timestamps"/> Include timestamps</label><br/>
              <label><input type="checkbox" name="with_transcript"/> Include verbatim transcript</label><br/><br/>
              <button type="submit">Generate Reports</button>
            </form>
          </body>
        </html>
        """

    @app.route("/process", methods=["POST"])
    def process():
        lang = request.form.get("lang", config["defaults"].get("language", "zh"))
        include_timestamps = bool(request.form.get("timestamps"))
        with_transcript = bool(request.form.get("with_transcript"))
        reports = request.form.get("reports", "").strip()
        formats = request.form.get("formats", "").strip()
        url = request.form.get("url", "").strip()
        upload = request.files.get("file")

        if not url and (upload is None or upload.filename == ""):
            return "Please provide a YouTube URL or upload an audio file.", 400

        if url:
            target = url
        else:
            upload_dir = os.path.join(config["paths"]["output_dir"], "uploads")
            ensure_dir(upload_dir)
            target = os.path.join(upload_dir, upload.filename)
            upload.save(target)

        job_id = f"job_{len(jobs)+1}"
        jobs[job_id] = {"status": "running", "target": target}

        def run_job():
            try:
                report_keys = [x.strip() for x in reports.split(",") if x.strip()] if reports else None
                export_formats = [x.strip() for x in formats.split(",") if x.strip()] if formats else config["defaults"].get("export_formats", ["md"])
                process_target(
                    target,
                    config=config,
                    lang=lang,
                    include_timestamps=include_timestamps,
                    with_transcript=with_transcript,
                    report_keys=report_keys,
                    tts_enabled=config["defaults"].get("tts", True),
                    export_formats=export_formats,
                    dry_run=False,
                )
                jobs[job_id]["status"] = "done"
            except Exception as e:
                jobs[job_id]["status"] = f"error: {e}"

        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        return jsonify({"job_id": job_id})

    @app.route("/status/<job_id>", methods=["GET"])
    def status(job_id):
        return jsonify(jobs.get(job_id, {"status": "unknown"}))

    app.run(host="0.0.0.0", port=port)
