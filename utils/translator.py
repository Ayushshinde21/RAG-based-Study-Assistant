import os
import requests


def translate_hindi_to_english(hindi_text: str) -> str:
    """
    Translate Hindi text to English using Sarvam AI.
    Returns English text.
    """
    if not hindi_text.strip():
        return ""

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in .env file")

    url = "https://api.sarvam.ai/translate"

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    # Sarvam allows max 1000 chars per request — split if needed
    chunks = _split_text(hindi_text, max_length=1000)
    translated_chunks = []

    for chunk in chunks:
        payload = {
            "input": chunk,
            "source_language_code": "hi-IN",
            "target_language_code": "en-IN",
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1",
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Sarvam Translate error {response.status_code}: {response.text}")

        result = response.json()
        translated_chunks.append(result.get("translated_text", ""))

    return " ".join(translated_chunks)


def _split_text(text: str, max_length: int = 1000) -> list:
    """
    Split long text into chunks of max_length characters.
    Splits at sentence boundaries where possible.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while len(text) > max_length:
        # try to split at last sentence boundary before max_length
        split_at = text.rfind("।", 0, max_length)   # Hindi full stop
        if split_at == -1:
            split_at = text.rfind(".", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at + 1].strip())
        text = text[split_at + 1:].strip()

    if text:
        chunks.append(text)

    return chunks
