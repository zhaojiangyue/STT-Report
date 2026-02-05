# YouTube to AI Reports & Audio Tool

This tool automates the process of converting YouTube videos into insightful reports and audio summaries using Google's Gemini models. It downloads audio, transcribes it (optional), and generates two types of reports in Chinese, along with a spoken audio version for children.

## 🚀 Features

- **YouTube to MP3**: Downloads and extracts high-quality audio from YouTube videos.
- **Smart Resuming**: Automatically skips steps that are already completed (download, upload, generation).
- **Dual Reporting**:
  - 🎓 **Professional Report (Chinese)**: Simple, jargon-free explanation for adults.
  - 🧸 **Children's Report (Chinese)**: Fun, engaging explanation for 10-12 year olds.
- **Audio Generation**: Converts the children's report into a natural Chinese audio file (MP3) using Gemini TTS.
- **Cost Efficient**: Skips re-uploading if the file is already in the Gemini Cloud cache.
- **Organization**: Keeps everything tidy in an `./output/` folder.

## 📦 Installation

1. **Prerequisites**:
   - Python 3.8+
   - [FFmpeg](https://ffmpeg.org/download.html) installed and added to your system PATH.

2. **Install Dependencies**:
   ```bash
   pip install google-genai yt-dlp tqdm python-dotenv
   ```

   ```

3. **Set API Key**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your Google Gemini API key:
   ```ini
   GEMINI_API_KEY=your_key_here
   ```

## 🛠️ Usage

### Basic Usage (Recommended)
Generates the reports and audio only (skips the slow verbatim transcript).
```bash
python stt.py https://www.youtube.com/watch?v=VIDEO_ID
```

### Full Processing
Includes a verbatim word-for-word transcript (can take longer for long videos).
```bash
python stt.py https://www.youtube.com/watch?v=VIDEO_ID --with-transcript
```

### Local Files
You can also process a local MP3 file:
```bash
python stt.py "my_lecture.mp3"
```

## 📂 Output Structure

All files are saved in the `output/` directory:

```text
output/
└── Video_Title_results/
    ├── Video_Title.mp3                             # Source audio
    ├── Video_Title_professional_chinese_report.md  # Adult summary
    ├── Video_Title_children_chinese_report.md      # Kids summary
    ├── Video_Title_children_report_chinese_audio.mp3 # Audio summary
    └── Video_Title_transcript.md                   # Verbatim transcript (if enabled)
```

## ⚠️ Notes

- **Initial Upload**: Large files (e.g., 3 hours) may take time to upload initially.
- **Timeouts**: The script handles network timeouts and retries automatically for robust processing.
- **Cache**: Uploaded files remain in Google's cloud cache for ~48 hours. The script detects this to save upload time.
