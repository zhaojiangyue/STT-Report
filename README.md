# STT-Report

YouTube/Audio → AI Reports pipeline with multi-language support, configurable prompts, batch processing, web UI, watch mode, API server, podcast feeds, export formats, plugins, and an intelligence layer.

## One-Page Quickstart

1. Install:
```bash
pip install -r requirements.txt
```
2. Set API key:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GEMINI_API_KEY=your_key_here
```
3. Run your first report:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional
```
4. Find outputs in:
```
output/<Title>_results/
```
Key files:
- `*_professional_en_report.md`
- `*_transcript.md` (if enabled)
- `*_children_en_audio.mp3` (if children report + TTS enabled)

Optional:
- Add timestamps: `--timestamps`
- Export PDF/DOCX: `--format pdf,docx`
- Web UI: `python stt.py --serve --port 8080`

## Features (aligned to ImprovementPlan)

- Multi-language reports (`--lang`)
- Configurable prompts (`config.yaml`, `prompts/`)
- Custom report types (config or `--reports`)
- Batch processing (`--batch`)
- Cost estimation (`--dry-run`)
- Progress persistence (checkpoint in output folder)
- Interactive report builder (`--interactive`)
- Comparison mode (`--compare`)
- Export formats: Markdown, PDF, DOCX, Notion (`--format`)
- Timestamps/chapters (`--timestamps`)
- Web UI dashboard (`--serve`)
- Plugin architecture (email, notion, obsidian, telegram)
- Watch mode (`--watch`)
- API server mode (`--serve` + `/process`)
- Podcast feed integration (`--feeds`)
- Intelligence layer (content type, quotes, fact check flags, follow-up questions, related content, knowledge graph)

## Installation

```bash
pip install -r requirements.txt
```

Set API key:
```bash
cp .env.example .env
```
Then edit `.env`:
```ini
GEMINI_API_KEY=your_key_here
```

## Usage

### Basic
```bash
python stt.py https://www.youtube.com/watch?v=VIDEO_ID
```

### Language
```bash
python stt.py my_lecture.mp3 --lang en
```

### Reports override
```bash
python stt.py my_lecture.mp3 --reports professional,children
```

### Timestamps
```bash
python stt.py my_lecture.mp3 --timestamps
```

### Dry run (cost estimate)
```bash
python stt.py my_lecture.mp3 --dry-run
```

### Batch
```bash
python stt.py --batch playlist.txt
python stt.py --batch ./incoming_audio
```

### Interactive builder
```bash
python stt.py --interactive my_lecture.mp3
```

### Compare
```bash
python stt.py --compare video1.mp3 video2.mp3
```

### Export formats
```bash
python stt.py my_lecture.mp3 --format pdf,docx,notion
```

### Web UI / API server
```bash
python stt.py --serve --port 8080
```

### Watch mode
```bash
python stt.py --watch ./incoming_audio
```

### Podcast feeds
```bash
python stt.py --feeds feeds.yaml
```
See `feeds.yaml.example` for format.

### QA Smoke Script
For a real-world QA pass that exercises most features:
```powershell
.\qa_smoke.ps1
```

Optional extended checks:
```powershell
$env:RUN_WEB_UI=1
$env:RUN_WATCH=1
$env:RUN_FEEDS=1
$env:RUN_PLUGINS=1
.\qa_smoke.ps1
```

## Config

`config.yaml` controls defaults, models, prompts, plugins, and intelligence features.

Key sections:
- `defaults`: language, reports, tts, timestamps, export_formats
- `models`: text/audio model ids
- `reports`: prompt/temperature
- `plugins`: enable and configure plugins
- `intelligence`: enable/disable post-processing

## Output

Each run creates an output folder:
```
output/
  Video_Title_results/
    Video_Title.mp3
    Video_Title_professional_zh_report.md
    Video_Title_children_zh_report.md
    Video_Title_children_zh_audio.mp3
    Video_Title_transcript.md
    content_type.json
    key_quotes.md
    fact_check.md
    follow_up_questions.md
    related_content.md
    entities.json
    checkpoint.json
```

## Test Cases (Detailed)

This section provides a comprehensive manual QA checklist aligned with tool features.

### Prerequisites
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Ensure `.env` contains `GEMINI_API_KEY`.
3. (Optional) Install extras:
   - Web UI: `pip install flask`
   - Feeds: `pip install feedparser`
   - Exports: `pip install reportlab python-docx`
   - Notion: `pip install notion-client`

### Core Pipeline
1. Basic run:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional
```
Expected:
- Output folder created under `output/`
- Professional report saved

2. With timestamps:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional --timestamps
```
Expected:
- Report includes timestamp section

3. With transcript:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional --with-transcript
```
Expected:
- `*_transcript.md` exists

4. Dry run cost estimate:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --dry-run
```
Expected:
- Prints duration, token estimate, USD estimate

### Config / Custom Reports
5. Add a new report type in `config.yaml`:
```yaml
reports:
  executive:
    temperature: 0.3
    prompt:
      file: prompts/professional.md
```
Run:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --reports executive --lang en
```
Expected:
- `*_executive_en_report.md` exists

### Batch + Watch
6. Batch file:
```text
# playlist.txt
https://www.youtube.com/watch?v=T9aRN5JkmL8
```
```bash
python stt.py --batch playlist.txt --lang en --reports professional
```
Expected:
- Same outputs as basic run

7. Watch mode:
```bash
python stt.py --watch ./incoming_audio
```
Expected:
- Dropping any `.mp3` into `incoming_audio/` triggers processing

### Comparison + Interactive
8. Comparison:
```bash
python stt.py --compare https://www.youtube.com/watch?v=T9aRN5JkmL8 https://www.youtube.com/watch?v=T9aRN5JkmL8
```
Expected:
- `output/<A>_vs_<B>_comparison/comparison_report.md`

9. Interactive:
```bash
python stt.py --interactive https://www.youtube.com/watch?v=T9aRN5JkmL8
```
Expected:
- Prompts for reports, language, timestamps, formats, custom prompt

### Export Formats
10. PDF/DOCX:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --format pdf,docx --lang en --reports professional
```
Expected:
- `.pdf` and `.docx` created in output folder

11. Notion export:
Configure `config.yaml` under `plugins.notion`, then:
```bash
python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --format notion --lang en --reports professional
```
Expected:
- New page created in Notion database

### Web UI / API Server
12. Run web UI:
```bash
python stt.py --serve --port 8080
```
Expected:
- Visit `http://localhost:8080` and submit a URL or file
  
13. API request:
```bash
curl -X POST http://localhost:8080/process -F "url=https://www.youtube.com/watch?v=T9aRN5JkmL8" -F "lang=en" -F "reports=professional"
```
Expected:
- JSON response with `job_id`
- `http://localhost:8080/status/<job_id>` returns status

### Podcast Feeds
14. Configure feeds:
```yaml
feeds:
  - name: "Example Podcast"
    url: "https://feeds.simplecast.com/yourfeed"
    reports: [professional]
    auto_process: true
```
Run:
```bash
python stt.py --feeds feeds.yaml
```
Expected:
- New episodes downloaded and processed

### Plugins
15. Enable plugin (example: Telegram):
```yaml
plugins:
  enabled: [telegram]
  config:
    telegram:
      bot_token: your_bot_token
      chat_id: your_chat_id
```
Run any job and verify:
- Notification sent to Telegram

### Intelligence Layer
16. After any run, verify these files exist in output folder:
- `content_type.json`
- `key_quotes.md`
- `fact_check.md`
- `follow_up_questions.md`
- `related_content.md`
- `entities.json`
- `knowledge_graph.json` (in `output/`)


## Architecture

```
stt/
  cli.py
  core.py
  downloaders/
  generators/
  exporters/
  plugins/
prompts/
tests/
```
