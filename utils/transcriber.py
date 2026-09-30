import os
import math
import tempfile
import subprocess
from faster_whisper import WhisperModel
from utils.translator import translate_hindi_to_english

model = WhisperModel("small", device="cpu", compute_type="int8")

# BatchedInferencePipeline (faster-whisper >= 1.1) batches audio segments and
# skips silence via VAD instead of decoding the whole file frame-by-frame —
# typically 2-4x faster than the plain model on CPU for lecture-style audio.
# Fall back to the plain model on older faster-whisper versions.
try:
    from faster_whisper import BatchedInferencePipeline
    batched_model = BatchedInferencePipeline(model=model)
except ImportError:
    batched_model = None


def detect_language(audio_path: str) -> str:
    _, info = model.transcribe(audio_path, beam_size=1)
    detected = info.language
    print(f"🌐 Detected language: {detected}")
    return detected


def transcribe_english(audio_path: str) -> str:
    if batched_model is not None:
        print("📝 Transcribing with Whisper (English, batched + VAD)...")
        segments, _ = batched_model.transcribe(
            audio_path, language="en", vad_filter=True, batch_size=16
        )
    else:
        print("📝 Transcribing with Whisper (English)...")
        segments, _ = model.transcribe(audio_path, language="en", vad_filter=True)
    transcript = " ".join([seg.text for seg in segments]).strip()
    print(f"✅ Transcription done! ({len(transcript)} characters)")
    return transcript


def transcribe_hindi(audio_path: str) -> str:
    print("📝 Transcribing with Sarvam AI (Hindi)...")

    hindi_text = _sarvam_transcribe(audio_path)

    print("🔄 Translating Hindi → English...")
    english_text = translate_hindi_to_english(hindi_text)

    print(f"✅ Done! ({len(english_text)} characters)")
    return english_text


def _get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def _split_audio(audio_path: str, output_dir: str, chunk_duration: int = 25):
    duration = _get_audio_duration(audio_path)

    if duration <= 30:
        return [audio_path]

    print(
        f"🎧 Audio duration: {duration:.1f} seconds. "
        f"Splitting into {chunk_duration}-second chunks..."
    )

    os.makedirs(output_dir, exist_ok=True)

    total_chunks = math.ceil(duration / chunk_duration)
    chunk_paths = []

    for i in range(total_chunks):
        start = i * chunk_duration
        output_path = os.path.join(
            output_dir,
            f"chunk_{i + 1:04d}.mp3"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-i",
                audio_path,
                "-t",
                str(chunk_duration),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "64k",
                output_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        chunk_paths.append(output_path)

    print(f"✂️ Created {len(chunk_paths)} audio chunks")

    return chunk_paths


def _sarvam_transcribe_single(audio_path: str) -> str:
    import requests

    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")

    url = "https://api.sarvam.ai/speech-to-text"

    with open(audio_path, "rb") as f:
        files = {
            "file": (
                os.path.basename(audio_path),
                f,
                "audio/mpeg"
            )
        }

        headers = {
            "api-subscription-key": api_key
        }

        data = {
            "language_code": "hi-IN",
            "model": "saaras:v3",
            "mode": "transcribe",
        }

        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Sarvam API error {response.status_code}: {response.text}"
        )

    result = response.json()

    transcript = result.get("transcript", "").strip()

    if not transcript:
        raise RuntimeError(
            f"Sarvam returned an empty transcript: {result}"
        )

    return transcript


def _sarvam_transcribe(audio_path: str) -> str:
    duration = _get_audio_duration(audio_path)

    if duration <= 30:
        print("🎙️ Audio is under 30 seconds. Sending directly to Sarvam...")
        return _sarvam_transcribe_single(audio_path)

    print(
        f"🎙️ Long audio detected: {duration / 60:.2f} minutes"
    )

    with tempfile.TemporaryDirectory(prefix="sarvam_chunks_") as temp_dir:
        chunk_paths = _split_audio(
            audio_path,
            temp_dir,
            chunk_duration=25,
        )

        # A 1-hour lecture is ~144 chunks. Calling Sarvam one chunk at a time
        # made this the slowest single step in the whole pipeline. Chunks are
        # independent API calls, so run several in parallel; ex.map keeps
        # results in the original order.
        from concurrent.futures import ThreadPoolExecutor

        print(f"📝 Sending {len(chunk_paths)} chunks to Sarvam (parallel)...")

        with ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(_sarvam_transcribe_single, chunk_paths))

        transcripts = [text for text in results if text]

        combined_text = " ".join(transcripts).strip()

        print(
            f"✅ Sarvam transcription completed "
            f"({len(transcripts)} chunks, "
            f"{len(combined_text)} characters)"
        )

        return combined_text


def transcribe(audio_path: str) -> str:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    lang = detect_language(audio_path)

    if lang == "hi":
        return transcribe_hindi(audio_path)
    else:
        return transcribe_english(audio_path)


def save_transcript(text: str, audio_path: str) -> str:
    os.makedirs("transcripts", exist_ok=True)

    base = os.path.splitext(
        os.path.basename(audio_path)
    )[0]

    output_path = os.path.join(
        "transcripts",
        f"{base}.txt"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(text)

    print(f"💾 Transcript saved: {output_path}")

    return output_path

