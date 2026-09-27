import os
from faster_whisper import WhisperModel
from utils.translator import translate_hindi_to_english

# Load model once
model = WhisperModel("small", device="cpu", compute_type="int8")


def detect_language(audio_path: str) -> str:
    """
    Detect the language of the audio file.
    """
    _, info = model.transcribe(audio_path, beam_size=1)
    detected = info.language
    print(f"🌐 Detected language: {detected}")
    return detected


def transcribe_english(audio_path: str) -> str:
    """
    Transcribe English audio using faster-whisper.
    """
    print("📝 Transcribing with Whisper (English)...")
    segments, _ = model.transcribe(audio_path, language="en")
    transcript = " ".join([seg.text for seg in segments]).strip()
    print(f"✅ Transcription done! ({len(transcript)} characters)")
    return transcript


def transcribe_hindi(audio_path: str) -> str:
    """
    Transcribe Hindi audio using Sarvam AI then translate to English.
    """
    print("📝 Transcribing with Sarvam AI (Hindi)...")
    hindi_text = _sarvam_transcribe(audio_path)
    print("🔄 Translating Hindi → English...")
    english_text = translate_hindi_to_english(hindi_text)
    print(f"✅ Done! ({len(english_text)} characters)")
    return english_text


def _sarvam_transcribe(audio_path: str) -> str:
    """
    Call Sarvam AI API for Hindi transcription.
    """
    import requests

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env")

    url = "https://api.sarvam.ai/speech-to-text"

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
        headers = {"api-subscription-key": api_key}
        data = {
            "language_code": "hi-IN",
            "model": "saarika:v2",
        }
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise RuntimeError(f"Sarvam API error {response.status_code}: {response.text}")

    return response.json().get("transcript", "")


def transcribe(audio_path: str) -> str:
    """
    Main entry point — auto detects language and transcribes.
    Always returns English text.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    lang = detect_language(audio_path)

    if lang == "hi":
        return transcribe_hindi(audio_path)
    else:
        return transcribe_english(audio_path)


def save_transcript(text: str, audio_path: str) -> str:
    """
    Save transcript to a .txt file.
    """
    os.makedirs("transcripts", exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join("transcripts", f"{base}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"💾 Transcript saved: {output_path}")
    return output_path
