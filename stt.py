import os
import time
import sys
import wave
import base64
import re
import shutil
import subprocess
from google import genai
from google.genai import types
from tqdm import tqdm

# ================= Configuration =================
# API Key Setup
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ Warning: 'python-dotenv' not installed. .env file might not be loaded.")

# API Key Setup
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ Error: API Key not found.")
    print("Please create a '.env' file with GEMINI_API_KEY=... OR set the environment variable.")
    print("Tip: Install python-dotenv with 'pip install python-dotenv' to use .env files.")
    sys.exit(1)
MODEL_ID = "gemini-3-pro-preview"
AUDIO_MODEL_ID = "gemini-2.5-flash-preview-tts"

def download_youtube_audio(url):
    """Downloads audio from YouTube using yt-dlp and returns the filename."""
    print(f"📺 Detecting YouTube URL. Downloading audio...")
    try:
        # Get just the title first
        cmd_get_title = ['yt-dlp', '--no-warnings', '--get-title', url]
        title = subprocess.check_output(cmd_get_title, text=True).strip()
        # Sanitize title (remove characters that cause issues in filenames)
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        mp3_filename = f"{safe_title}.mp3"
        output_folder_path = os.path.join("output", f"{safe_title}_results", mp3_filename)
        
        # Check if already downloaded (in root or moved to output folder)
        if os.path.exists(mp3_filename):
            print(f"⏩ Audio already downloaded: {mp3_filename}")
            return mp3_filename
        elif os.path.exists(output_folder_path):
            print(f"⏩ Audio found in output folder: {output_folder_path}")
            return output_folder_path
            
        # Download and convert to mp3
        cmd_download = ['yt-dlp', '--no-warnings', '-x', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s', url]
        subprocess.run(cmd_download, check=True)
        print(f"✅ Downloaded: {mp3_filename}")
        return mp3_filename
    except Exception as e:
        print(f"❌ YouTube download failed: {e}")
        sys.exit(1)

def get_existing_file(client, filename):
    """Checks if a file with the same name already exists and is active on the server."""
    print("🔍 Checking cloud cache...", end="")
    try:
        # Iterate through cloud files
        for file in client.files.list():
            if file.display_name == filename:
                if file.state.name == "ACTIVE":
                    print(" ✅ Found active cache! (Skipping upload)")
                    return file
                elif file.state.name == "FAILED":
                    print(" ❌ Found corrupted file, deleting and re-uploading.")
                    client.files.delete(name=file.name)
                    return None
        print(" ☁️ No cache found, preparing to upload.")
        return None
    except Exception:
        print(" (Cache check failed, proceeding to upload)")
        return None

def text_to_speech(client, text, output_filename):
    """Translates text to speech using Gemini and saves as WAV with robust error handling."""
    print(f"🔊 Generating Audio for: {output_filename} ...")
    
    # 1. Advanced Chunking (Split by sentence if needed)
    chunks = []
    current_chunk = ""
    
    # Split by newlines first
    raw_lines = text.split('\n')
    
    for line in raw_lines:
        line = line.strip()
        if not line: continue
        
        # If a single line is huge (e.g. > 500 chars), split it further
        if len(line) > 500:
            # Split by Chinese/English sentence terminators
            sub_parts = re.split(r'([。！？.!?])', line)
            # Re-assemble keeping delimiters
            sentences = []
            for j in range(0, len(sub_parts) - 1, 2):
                sentences.append(sub_parts[j] + sub_parts[j+1])
            if len(sub_parts) % 2 != 0: 
                sentences.append(sub_parts[-1])
            
            for sent in sentences:
                if len(current_chunk) + len(sent) > 500:
                    chunks.append(current_chunk)
                    current_chunk = sent
                else:
                    current_chunk += sent
        else:
            if len(current_chunk) + len(line) > 500:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
    
    if current_chunk: chunks.append(current_chunk)

    all_pcm_data = bytearray()
    
    # 2. Processing
    print(f"   Total chunks to process: {len(chunks)}")
    
    with tqdm(total=len(chunks), desc="Synthesizing Audio") as pbar:
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): 
                pbar.update(1)
                continue
            
            # Retry mechanism for this chunk
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Verbose logging to prevent "stuck" feeling
                    # print(f"   [Chunk {i+1}/{len(chunks)}] Attempt {attempt+1}...") 
                    
                    response = client.models.generate_content(
                        model=AUDIO_MODEL_ID,
                        contents=f"Please read this text naturally in Chinese (Mandarin): {chunk}",
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"]
                        )
                    )
                    
                    if response.candidates:
                        found_audio = False
                        for part in response.candidates[0].content.parts:
                            if part.inline_data and "audio" in part.inline_data.mime_type:
                                data = part.inline_data.data
                                if isinstance(data, str):
                                    data = base64.b64decode(data)
                                all_pcm_data.extend(data)
                                found_audio = True
                        if found_audio:
                            break # Success, exit retry loop
                    else:
                         print(f" (Empty response for chunk {i})")

                except Exception as e:
                    print(f"   ⚠️ Chunk {i+1} error (Attempt {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        print(f"   ❌ Chunk {i+1} failed permanently.")
                    else:
                        time.sleep(3 * (attempt + 1)) # Increased Backoff
            
            pbar.update(1)
            time.sleep(2) # Increased politeness delay 

    # 3. Save (WAV → MP3 conversion)
    if len(all_pcm_data) > 0:
        # Save as temp WAV first
        temp_wav = output_filename.replace('.mp3', '_temp.wav')
        with wave.open(temp_wav, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2) 
            wav_file.setframerate(24000)
            wav_file.writeframes(all_pcm_data)
        
        # Convert to MP3 using ffmpeg
        if output_filename.endswith('.mp3'):
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', temp_wav,
                    '-codec:a', 'libmp3lame', '-qscale:a', '2',
                    output_filename
                ], check=True, capture_output=True)
                os.remove(temp_wav)  # Clean up temp file
                print(f"✅ Audio saved to: {output_filename}")
            except Exception as e:
                print(f"⚠️ FFmpeg conversion failed: {e}")
                print(f"   WAV file saved as: {temp_wav}")
        else:
            # If not mp3, just rename
            os.rename(temp_wav, output_filename)
            print(f"✅ Audio saved to: {output_filename}")
    else:
        print("❌ No audio data generated.")

def generate_with_retry(client, model, contents, config, max_retries=5):
    """Generate content with retry logic for handling server disconnects."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            error_msg = str(e).lower()
            # Retry on connection/timeout errors
            if any(x in error_msg for x in ['disconnect', 'timeout', 'reset', 'connection']):
                wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s
                print(f"   ⚠️ Attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"   ⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                # Non-retryable error
                raise

import threading

def show_progress(message, stop_event):
    """Show a spinner while processing."""
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        print(f"\r{spinners[i % len(spinners)]} {message}...", end="", flush=True)
        time.sleep(0.2)
        i += 1
    print("\r" + " " * (len(message) + 10), end="\r")  # Clear line

def generate_with_progress(client, model, contents, config, message, max_retries=5):
    """Generate content with progress spinner and retry logic."""
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_progress, args=(message, stop_event))
    spinner_thread.start()
    
    try:
        response = generate_with_retry(client, model, contents, config, max_retries)
        return response
    finally:
        stop_event.set()
        spinner_thread.join()

def analyze_video(video_path, skip_transcript=False):
    # 0. File Check
    if not os.path.exists(video_path):
        print(f"❌ Error: File '{video_path}' not found.")
        return

    # Get filename
    display_name = os.path.basename(video_path)
    base_filename = os.path.splitext(display_name)[0]
    output_dir = os.path.join("output", f"{base_filename}_results")

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory: {output_dir}")
    else:
        print(f"📁 Using output directory: {output_dir}")
    
    # Move source audio into results folder
    source_in_folder = os.path.join(output_dir, display_name)
    if not os.path.exists(source_in_folder) and os.path.exists(video_path):
        shutil.move(video_path, source_in_folder)
        print(f"📦 Moved source audio to: {source_in_folder}")

    # Helper to migrate old files
    def get_file_path(suffix):
        filename = f"{base_filename}{suffix}"
        legacy_path = filename
        new_path = os.path.join(output_dir, filename)
        
        # If file exists in root but not in folder, move it
        if os.path.exists(legacy_path) and not os.path.exists(new_path):
            print(f"📦 Moving legacy file {filename} to {output_dir}...")
            shutil.move(legacy_path, new_path)
            
        return new_path

    # 1. Initialize Client (with extended timeout for large uploads)
    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=1800000)  # 30 minutes in milliseconds
    )

    # 2. Upload File (with cache check)
    myfile = get_existing_file(client, display_name)

    if not myfile:
        print(f"🚀 Uploading: {video_path} ...")
        
        # Retry logic for upload
        max_upload_retries = 3
        for attempt in range(max_upload_retries):
            try:
                myfile = client.files.upload(file=video_path, config={'display_name': display_name}) 
                print(f"✅ Upload successful: {myfile.name}")
                break # Success
            except Exception as e:
                print(f"   ⚠️ Upload attempt {attempt+1} failed: {e}")
                if attempt == max_upload_retries - 1:
                    print(f"❌ Upload failed permanently after {max_upload_retries} attempts.")
                    return
                time.sleep(5) # Wait before retry

    # 3. Wait for Processing (with tqdm)
    print("⏳ Waiting for Google to process audio...")
    with tqdm(total=100, bar_format='{desc}: {bar} {elapsed}', desc="Processing") as pbar:
        while True:
            myfile = client.files.get(name=myfile.name)
            if myfile.state.name == "ACTIVE":
                pbar.update(100 - pbar.n)
                break
            elif myfile.state.name == "FAILED":
                print("\n❌ Processing failed. Please check the file format.")
                return
            else:
                if pbar.n < 90: pbar.update(5)
                time.sleep(5)

    print(f"\n✅ Ready. Analyzing with {MODEL_ID}...")

    # --- Task 1: Transcript (Verbatim) ---
    transcript_prompt = """
    【Objective】
    Provide a verbatim, word-for-word transcript of the audio content.
    Do not summarize. Do not leave out details. Capture every spoken word as accurately as possible.
    【Output Format】
    Markdown document titled "# Verbatim Transcript".
    """

    # --- Task 2: Professional Report (Simple/Accessible - in Chinese) ---
    adult_report_prompt = """
    【Role】
    You are a friendly public educator writing in Chinese (Mandarin).
    【Objective】
    Explain the video/audio content in simple, accessible Chinese for adults with no technical background.
    - Avoid jargon. If you must use a technical term, explain it immediately in plain Chinese.
    - Focus on "这对我有什么意义？" and "它是如何运作的？" in simple terms.
    - Use analogies from daily life (烹饪、开车、种菜, etc.).
    【Output Format】
    Markdown report in Chinese:
    # 这是什么？（简单解释）
    # 要点总结
    # 为什么重要？
    """

    # --- Task 3: Children's Report (Direct Chinese) ---
    child_cn_prompt = """
    【Role】
    You are a friendly science teacher for kids.
    【Objective】
    Explain the content to a 10-12 year old child in **natural, engaging Chinese (Mandarin)**.
    - Use fun, encouraging, and very simple Chinese.
    - Use emojis.
    - Use analogies kids understand (games, school, toys).
    【Output Format】
    Markdown report in Chinese.
    """

    # Define filenames with path handling
    transcript_file = get_file_path("_transcript.md")
    adult_file = get_file_path("_professional_chinese_report.md")
    child_cn_file = get_file_path("_children_chinese_report.md")
    audio_file = get_file_path("_children_report_chinese_audio.mp3")

    try:
        # Skip transcript unless --with-transcript flag is used
        if skip_transcript:
            print("⏭️  Transcript generation disabled (use --with-transcript to enable)")
        
        # 1. Generate Verbatim Transcript (first or last depending on flag)
        def do_transcript():
            if os.path.exists(transcript_file):
                print(f"⏩ Transcript already exists: {transcript_file}")
            else:
                transcript_response = generate_with_progress(
                    client, MODEL_ID,
                    contents=[myfile, transcript_prompt],
                    config=types.GenerateContentConfig(temperature=0.1),
                    message="📝 Generating Verbatim Transcript"
                )
                with open(transcript_file, "w", encoding="utf-8") as f:
                    f.write(transcript_response.text)
                print(f"✅ Saved: {transcript_file}")
        
        if not skip_transcript:
            do_transcript()

        # 2. Generate Professional Report
        if os.path.exists(adult_file):
            print(f"⏩ Professional Report already exists: {adult_file}")
        else:
            adult_response = generate_with_progress(
                client, MODEL_ID,
                contents=[myfile, adult_report_prompt],
                config=types.GenerateContentConfig(temperature=0.3),
                message="💼 Generating Professional Report"
            )
            with open(adult_file, "w", encoding="utf-8") as f:
                f.write(adult_response.text)
            print(f"✅ Saved: {adult_file}")

        # 3. Generate Children's Chinese Report
        child_cn_text = ""
        if os.path.exists(child_cn_file):
            print(f"⏩ Children's Chinese Report already exists: {child_cn_file}")
            with open(child_cn_file, "r", encoding="utf-8") as f:
                child_cn_text = f.read()
        else:
            child_cn_response = generate_with_progress(
                client, MODEL_ID,
                contents=[myfile, child_cn_prompt],
                config=types.GenerateContentConfig(temperature=0.5),
                message="🧸 Generating Children's Report (Chinese)"
            )
            child_cn_text = child_cn_response.text
            with open(child_cn_file, "w", encoding="utf-8") as f:
                f.write(child_cn_text)
            print(f"✅ Saved: {child_cn_file}")

        # 4. Generate Audio from Chinese Report
        if os.path.exists(audio_file):
             print(f"⏩ Audio already exists: {audio_file}")
        else:
            print("\n🇨🇳 Creating Chinese Audio...")
            if not child_cn_text:
                # Reload if needed
                if os.path.exists(child_cn_file):
                    with open(child_cn_file, "r", encoding="utf-8") as f:
                        child_cn_text = f.read()
                else:
                    raise FileNotFoundError("Chinese report missing, cannot generate audio.")
            
            text_to_speech(client, child_cn_text, audio_file)

        # 5. Generate transcript only if --with-transcript was used
        if not skip_transcript:
            print("\n📝 Now generating transcript...")
            do_transcript()

        print("\n" + "="*30)
        print(f"SUCCESS: All files located in '{output_dir}/'")
        print("="*30)

    except Exception as e:
        print(f"\n❌ Error during generation: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube to Transcript & Reports")
    parser.add_argument("input", nargs="?", help="Audio file or YouTube URL")
    parser.add_argument("--with-transcript", action="store_true", 
                        help="Also generate verbatim transcript (slow for long audio)")
    args = parser.parse_args()
    
    if args.input:
        input_target = args.input
        
        # Check if it's a YouTube URL
        if "youtube.com/" in input_target or "youtu.be/" in input_target:
            target_file = download_youtube_audio(input_target)
        else:
            target_file = input_target
            
        analyze_video(target_file, skip_transcript=not args.with_transcript)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python stt.py audio.mp3                      # Reports only (default)")
        print("  python stt.py https://youtu.be/xxx           # Reports only")  
        print("  python stt.py https://youtu.be/xxx --with-transcript  # Include transcript")
