import os
import math
import tempfile
import subprocess
import numpy as np
from faster_whisper import WhisperModel
from utils.translator import translate_hindi_to_english
from utils.http_retry import post_with_retry, provider_max_workers

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


def load_audio(audio_path: str, sr: int = 16000) -> np.ndarray:
    """
    Decode any audio file to 16 kHz mono float32 with the ffmpeg binary.
    Passing this array to Whisper avoids faster-whisper's own PyAV decoder, which
    crashes ("open() got an unexpected keyword argument 'metadata_errors'") when
    the installed `av` version doesn't match faster-whisper.
    """
    cmd = ["ffmpeg", "-nostdin", "-threads", "0", "-i", audio_path,
           "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"]
    try:
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
    except FileNotFoundError:
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and make sure it is on your PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Could not decode the audio: " + e.stderr.decode(errors="ignore")[-300:])
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0


def load_audio_window(audio_path: str, start_seconds: float = 0, duration_seconds: float = 30, sr: int = 16000) -> np.ndarray:
    """Decode only a small time window so language detection does not load hours of audio."""
    cmd = [
        "ffmpeg", "-nostdin", "-threads", "0", "-ss", str(max(0, start_seconds)),
        "-i", audio_path, "-t", str(max(1, duration_seconds)), "-f", "s16le",
        "-ac", "1", "-ar", str(sr), "-",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
    except FileNotFoundError:
        raise RuntimeError("ffmpeg was not found. Install ffmpeg and make sure it is on your PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Could not decode an audio sample: " + e.stderr.decode(errors="ignore")[-300:])
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0


def detect_language(audio_path: str, audio=None) -> str:
    sample = audio if audio is not None else load_audio_window(audio_path, 0, 30)
    if not len(sample):
        raise RuntimeError("Could not read audio from the beginning of this recording.")
    _, info = model.transcribe(sample, beam_size=1)
    detected = info.language
    print(f"🌐 Detected language: {detected}")
    return detected


def transcribe_english(audio_path: str) -> str:
    """Back-compat: plain text only, no timestamps."""
    segments = transcribe_english_segments(audio_path)
    return " ".join(s["text"] for s in segments).strip()


def transcribe_english_segments(
    audio_path: str,
    audio=None,
    language: str = "en",
    task: str = "transcribe",
) -> list[dict]:
    """
    Same as transcribe_english but keeps each segment's start/end time —
    Whisper returns these for free, we just weren't keeping them before.
    Needed so chat answers can cite "see 14:32" instead of just quoting text.
    """
    if audio is None:
        audio = load_audio(audio_path)
    if batched_model is not None:
        print(f"📝 Processing audio with Whisper (language={language}, task={task}, batched + VAD)...")
        segments, _ = batched_model.transcribe(
            audio, language=language, task=task, vad_filter=True, batch_size=16
        )
    else:
        print(f"📝 Processing audio with Whisper (language={language}, task={task})...")
        segments, _ = model.transcribe(audio, language=language, task=task, vad_filter=True)

    def _collect(segs):
        return [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            for seg in segs if seg.text.strip()
        ]

    result = _collect(segments)
    if not result:
        # The silence filter (VAD) can wrongly discard everything on quiet or
        # music-heavy audio. Retry once with it off before giving up.
        print("⚠️ No speech found with VAD on. Retrying without VAD...")
        segments, _ = model.transcribe(audio, language=language, task=task, vad_filter=False)
        result = _collect(segments)
    total_chars = sum(len(s["text"]) for s in result)
    print(f"✅ Transcription done! ({total_chars} characters, {len(result)} segments)")
    return result


def transcribe_hindi(audio_path: str) -> str:
    """Back-compat: plain text only, no timestamps."""
    segments = transcribe_hindi_segments(audio_path)
    return " ".join(s["text"] for s in segments).strip()


def transcribe_hindi_segments(audio_path: str, progress_callback=None) -> list[dict]:
    """
    Same as transcribe_hindi but keeps a timestamp per 25-second Sarvam
    chunk (coarser than Whisper's segment-level timestamps, but still
    enough to cite "around 14:30" in an answer).
    """
    print("📝 Transcribing with Sarvam AI (Hindi)...")
    hindi_chunks = _sarvam_transcribe_chunks(audio_path, progress_callback=progress_callback)

    print("🔄 Translating Hindi → English...")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    english_texts = [""] * len(hindi_chunks)
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(translate_hindi_to_english, chunk["text"]): index
            for index, chunk in enumerate(hindi_chunks)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            english_texts[futures[future]] = future.result()
            _report_progress(progress_callback, f"Translating Hindi segment {completed} of {len(hindi_chunks)}")

    result = [
        {"start": c["start"], "end": c["end"], "text": text.strip()}
        for c, text in zip(hindi_chunks, english_texts) if text.strip()
    ]
    total_chars = sum(len(s["text"]) for s in result)
    print(f"✅ Done! ({total_chars} characters, {len(result)} segments)")
    return result


def _get_audio_duration(audio_path: str) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("ffprobe was not found. Install ffmpeg and make sure ffprobe is on your PATH.")
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or "").strip()[-300:]
        raise RuntimeError("Could not read the audio duration with ffprobe. " + detail)

    try:
        duration = float(result.stdout.strip())
    except ValueError:
        raise RuntimeError("ffprobe did not return a valid audio duration.")
    if not math.isfinite(duration) or duration < 0:
        raise RuntimeError("ffprobe returned an invalid audio duration.")
    return duration


def _split_audio(audio_path: str, output_dir: str, chunk_duration: int = 25, progress_callback=None):
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

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
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
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except FileNotFoundError:
            raise RuntimeError("ffmpeg was not found. Install ffmpeg and make sure it is on your PATH.")
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip()[-300:]
            raise RuntimeError(
                f"FFmpeg could not prepare audio segment {i + 1} of {total_chunks}. {detail}"
            ) from exc

        chunk_paths.append(output_path)
        progress_interval = max(1, total_chunks // 20)
        if progress_callback is not None and ((i + 1) % progress_interval == 0 or i + 1 == total_chunks):
            try:
                progress_callback(f"Preparing audio segments {i + 1} of {total_chunks}")
            except Exception:
                pass

    print(f"✂️ Created {len(chunk_paths)} audio chunks")

    return chunk_paths


def _sarvam_transcribe_single(audio_path: str) -> str:
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")

    url = "https://api.sarvam.ai/speech-to-text"

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    files = {
        "file": (
            os.path.basename(audio_path),
            audio_bytes,
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

    response = post_with_retry(
        url,
        headers=headers,
        files=files,
        data=data,
        timeout=(10, 120),
        max_attempts=3,
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


def _sarvam_transcribe_chunks(audio_path: str, chunk_duration: int = 25, progress_callback=None) -> list[dict]:
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
        chunk_paths = _split_audio(
            audio_path, temp_dir, chunk_duration=chunk_duration, progress_callback=progress_callback
        )

        # A 1-hour lecture is ~144 chunks. Calling Sarvam one chunk at a time
        # made this the slowest single step in the whole pipeline. Chunks are
        # independent API calls, so run several in parallel; ex.map keeps
        # results in the original order.
        from concurrent.futures import ThreadPoolExecutor, as_completed

        print(f"📝 Sending {len(chunk_paths)} chunks to Sarvam (parallel)...")
        results = [""] * len(chunk_paths)
        with ThreadPoolExecutor(max_workers=provider_max_workers()) as ex:
            futures = {
                ex.submit(_sarvam_transcribe_single, chunk_path): index
                for index, chunk_path in enumerate(chunk_paths)
            }
            for completed, future in enumerate(as_completed(futures), start=1):
                results[futures[future]] = future.result()
                _report_progress(progress_callback, f"Transcribing Hindi audio chunk {completed} of {len(chunk_paths)}")

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


def _report_progress(progress_callback, message: str):
    if progress_callback is not None:
        try:
            progress_callback(message)
        except Exception:
            pass


def _transcribe_english_in_chunks(
    audio_path: str,
    duration: float,
    progress_callback=None,
    language: str = "en",
    task: str = "transcribe",
) -> list[dict]:
    """Transcribe long recordings in small windows to keep peak memory bounded."""
    try:
        chunk_seconds = int(os.getenv("WHISPER_CHUNK_SECONDS", "300"))
    except ValueError:
        chunk_seconds = 300
    chunk_seconds = max(60, min(chunk_seconds, 900))

    if duration <= chunk_seconds:
        action = "Translating lecture to English" if task == "translate" else "Transcribing lecture"
        _report_progress(progress_callback, action)
        audio = load_audio(audio_path)
        try:
            return transcribe_english_segments(
                audio_path, audio, language=language, task=task
            )
        finally:
            del audio
            import gc
            gc.collect()

    with tempfile.TemporaryDirectory(prefix="whisper_chunks_") as temp_dir:
        chunk_paths = _split_audio(audio_path, temp_dir, chunk_duration=chunk_seconds, progress_callback=progress_callback)
        if not chunk_paths:
            raise RuntimeError("Could not split the recording into transcription windows.")

        all_segments = []
        total = len(chunk_paths)
        for index, chunk_path in enumerate(chunk_paths):
            _report_progress(
                progress_callback,
                f"Transcribing audio window {index + 1} of {total} ({(index * chunk_seconds) // 60}-{min(((index + 1) * chunk_seconds), duration) // 60} min)",
            )
            chunk_segments = transcribe_english_segments(
                chunk_path, language=language, task=task
            )
            offset = index * chunk_seconds
            for segment in chunk_segments:
                all_segments.append({
                    "start": float(segment["start"]) + offset,
                    "end": float(segment["end"]) + offset,
                    "text": segment["text"],
                })
            del chunk_segments
            import gc
            gc.collect()

        return all_segments


def transcribe_with_timestamps(audio_path: str, progress_callback=None) -> list[dict]:
    """
    Transcribe a recording without loading its full decoded audio into memory.
    Returns timestamped segments, including offsets for long audio windows.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    duration = _get_audio_duration(audio_path)
    if duration < 1:
        raise RuntimeError(
            f"The audio file contains no usable audio ({duration:.1f} seconds). "
            "The download was probably incomplete. Try again or upload the file."
        )

    sample = load_audio_window(audio_path, 0, min(30, duration))
    peak = float(np.abs(sample).max()) if len(sample) else 0.0
    if peak < 0.001 and duration > 30:
        sample_starts = sorted({min(60.0, max(0.0, duration - 30.0)), max(0.0, duration / 2 - 15.0)})
        for sample_start in sample_starts:
            candidate = load_audio_window(audio_path, sample_start, min(30, duration - sample_start))
            candidate_peak = float(np.abs(candidate).max()) if len(candidate) else 0.0
            if candidate_peak > peak:
                sample, peak = candidate, candidate_peak
            else:
                del candidate
            if peak >= 0.001:
                break
    print(f"🔊 Audio: {duration:.1f}s long, detection-sample peak {peak:.3f}")
    if not len(sample):
        raise RuntimeError("The audio track could not be decoded. Try another video or upload the recording again.")
    if peak < 0.001:
        raise RuntimeError("The sampled audio appears silent. Check that the recording contains audible speech.")

    lang = detect_language(audio_path, sample)
    del sample
    import gc
    gc.collect()

    if lang == "hi" and os.getenv("SARVAM_API_KEY"):
        _report_progress(progress_callback, "Transcribing Hindi audio in API-sized chunks")
        return transcribe_hindi_segments(audio_path, progress_callback=progress_callback)

    if lang == "en":
        return _transcribe_english_in_chunks(
            audio_path, duration, progress_callback, language="en", task="transcribe"
        )

    _report_progress(
        progress_callback,
        f"Translating detected {lang} speech to English with local Whisper",
    )
    return _transcribe_english_in_chunks(
        audio_path, duration, progress_callback, language=lang, task="translate"
    )


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