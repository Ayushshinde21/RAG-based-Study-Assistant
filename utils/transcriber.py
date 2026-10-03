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
    """Back-compat: plain text only, no timestamps."""
    segments = transcribe_english_segments(audio_path)
    return " ".join(s["text"] for s in segments).strip()


def transcribe_english_segments(audio_path: str) -> list[dict]:
    """
    Same as transcribe_english but keeps each segment's start/end time —
    Whisper returns these for free, we just weren't keeping them before.
    Needed so chat answers can cite "see 14:32" instead of just quoting text.
    """
    if batched_model is not None:
        print("📝 Transcribing with Whisper (English, batched + VAD)...")
        segments, _ = batched_model.transcribe(
            audio_path, language="en", vad_filter=True, batch_size=16
        )
    else:
        print("📝 Transcribing with Whisper (English)...")
        segments, _ = model.transcribe(audio_path, language="en", vad_filter=True)

    result = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments if seg.text.strip()
    ]
    total_chars = sum(len(s["text"]) for s in result)
    print(f"✅ Transcription done! ({total_chars} characters, {len(result)} segments)")
    return result


def transcribe_hindi(audio_path: str) -> str:
    """Back-compat: plain text only, no timestamps."""
    segments = transcribe_hindi_segments(audio_path)
    return " ".join(s["text"] for s in segments).strip()


def transcribe_hindi_segments(audio_path: str) -> list[dict]:
    """
    Same as transcribe_hindi but keeps a timestamp per 25-second Sarvam
    chunk (coarser than Whisper's segment-level timestamps, but still
    enough to cite "around 14:30" in an answer).
    """
    print("📝 Transcribing with Sarvam AI (Hindi)...")
    hindi_chunks = _sarvam_transcribe_chunks(audio_path)

    print("🔄 Translating Hindi → English...")
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as ex:
        english_texts = list(ex.map(
            lambda c: translate_hindi_to_english(c["text"]), hindi_chunks
        ))

    result = [
        {"start": c["start"], "end": c["end"], "text": text.strip()}
        for c, text in zip(hindi_chunks, english_texts) if text.strip()
    ]
    total_chars = sum(len(s["text"]) for s in result)
    print(f"✅ Done! ({total_chars} characters, {len(result)} segments)")
    return result


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


def _sarvam_transcribe_chunks(audio_path: str, chunk_duration: int = 25) -> list[dict]:
    """
    Splits audio into fixed-duration chunks, transcribes each via Sarvam in
    parallel, and returns them WITH their start/end time (chunk index *
    chunk_duration). This is the shared building block behind both
    _sarvam_transcribe() (plain text) and transcribe_hindi_segments()
    (timestamped).
    """
    duration = _get_audio_duration(audio_path)

    if duration <= 30:
        print("🎙️ Audio is under 30 seconds. Sending directly to Sarvam...")
        text = _sarvam_transcribe_single(audio_path)
        return [{"start": 0.0, "end": duration, "text": text}] if text else []

    print(f"🎙️ Long audio detected: {duration / 60:.2f} minutes")

    with tempfile.TemporaryDirectory(prefix="sarvam_chunks_") as temp_dir:
        chunk_paths = _split_audio(audio_path, temp_dir, chunk_duration=chunk_duration)

        # A 1-hour lecture is ~144 chunks. Calling Sarvam one chunk at a time
        # made this the slowest single step in the whole pipeline. Chunks are
        # independent API calls, so run several in parallel; ex.map keeps
        # results in the original order.
        from concurrent.futures import ThreadPoolExecutor

        print(f"📝 Sending {len(chunk_paths)} chunks to Sarvam (parallel)...")

        with ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(_sarvam_transcribe_single, chunk_paths))

        chunks = [
            {
                "start": i * chunk_duration,
                "end": min((i + 1) * chunk_duration, duration),
                "text": text,
            }
            for i, text in enumerate(results) if text
        ]

        print(f"✅ Sarvam transcription completed ({len(chunks)} chunks)")
        return chunks


def _sarvam_transcribe(audio_path: str) -> str:
    """Back-compat: plain combined text, no timestamps."""
    chunks = _sarvam_transcribe_chunks(audio_path)
    return " ".join(c["text"] for c in chunks).strip()


def transcribe(audio_path: str) -> str:
    """Back-compat: plain text only, no timestamps."""
    segments = transcribe_with_timestamps(audio_path)
    return " ".join(s["text"] for s in segments).strip()


def transcribe_with_timestamps(audio_path: str) -> list[dict]:
    """
    Main entry point. Returns a list of {"start", "end", "text"} segments
    instead of one joined string, so downstream chunking can attach a
    timestamp to every chunk and chat answers can cite "see 14:32".
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    lang = detect_language(audio_path)

    if lang == "hi":
        return transcribe_hindi_segments(audio_path)
    else:
        return transcribe_english_segments(audio_path)


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def save_transcript(segments, audio_path: str) -> str:
    """
    Writes one timestamped line per segment, e.g. "[05:20] ...text...".
    core/chunker.py parses this format so every chunk can keep an
    approximate start time. Accepts a plain string too (old call signature)
    for backward compatibility — in that case no timestamps are written.
    """
    os.makedirs("transcripts", exist_ok=True)

    base = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join("transcripts", f"{base}.txt")

    if isinstance(segments, str):
        content = segments
    else:
        content = "\n".join(
            f"[{format_timestamp(s['start'])}] {s['text']}"
            for s in segments if s.get("text", "").strip()
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"💾 Transcript saved: {output_path}")

    return output_path