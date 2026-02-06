import base64
import time
import wave
import subprocess
import re

from google.genai import types
from tqdm import tqdm


def text_to_speech(client, model_id, text, output_filename, language_name):
    print(f"Generating Audio for: {output_filename} ...")
    chunks = []
    current_chunk = ""
    raw_lines = text.split("\n")
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        if len(line) > 500:
            sub_parts = re.split(r"([.!?。！？])", line)
            sentences = []
            for j in range(0, len(sub_parts) - 1, 2):
                sentences.append(sub_parts[j] + sub_parts[j + 1])
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
    if current_chunk:
        chunks.append(current_chunk)

    all_pcm_data = bytearray()
    print(f"   Total chunks to process: {len(chunks)}")
    with tqdm(total=len(chunks), desc="Synthesizing Audio") as pbar:
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                pbar.update(1)
                continue
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=f"Please read this text naturally in {language_name}: {chunk}",
                        config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
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
                            break
                    else:
                        print(f" (Empty response for chunk {i})")
                except Exception as e:
                    print(f"   Warning: Chunk {i+1} error (Attempt {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        print(f"   Chunk {i+1} failed permanently.")
                    else:
                        time.sleep(3 * (attempt + 1))
            pbar.update(1)
            time.sleep(2)

    if len(all_pcm_data) > 0:
        temp_wav = output_filename.replace(".mp3", "_temp.wav")
        with wave.open(temp_wav, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(all_pcm_data)

        if output_filename.endswith(".mp3"):
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        temp_wav,
                        "-codec:a",
                        "libmp3lame",
                        "-qscale:a",
                        "2",
                        output_filename,
                    ],
                    check=True,
                    capture_output=True,
                )
                import os
                os.remove(temp_wav)
                print(f"Audio saved to: {output_filename}")
            except Exception as e:
                print(f"FFmpeg conversion failed: {e}")
                print(f"   WAV file saved as: {temp_wav}")
        else:
            import os
            os.rename(temp_wav, output_filename)
            print(f"Audio saved to: {output_filename}")
    else:
        print("No audio data generated.")
