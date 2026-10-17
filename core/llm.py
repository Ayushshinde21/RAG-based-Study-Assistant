"""Shared Gemini LLM configuration for the study assistant."""

import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

MODEL_NAME = "gemini-3.8-flash"


def get_gemini_llm(*, response_mime_type: str | None = None) -> ChatGoogleGenerativeAI:
    """Create the configured Gemini model using the project's API key."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in .env. Add your Gemini API key and restart the app."
        )

    config: dict[str, Any] = {
        "model": MODEL_NAME,
        "api_key": api_key,
        "temperature": 1.0,
        "thinking_level": "low",
        "max_retries": 2,
        "timeout": 60,
    }
    if response_mime_type:
        config["response_mime_type"] = response_mime_type

    return ChatGoogleGenerativeAI(**config)


def response_text(message: Any) -> str:
    """Extract readable text from LangChain messages and streaming chunks."""
    if isinstance(message, str):
        return message.strip()

    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                if part.get("type") in {"text", "output_text"}:
                    value = part.get("text")
                    if isinstance(value, str):
                        text_parts.append(value)
            else:
                value = getattr(part, "text", None)
                if isinstance(value, str):
                    text_parts.append(value)
        result = "".join(text_parts).strip()
        if result:
            return result

    text_value = getattr(message, "text", None)
    if isinstance(text_value, str):
        return text_value.strip()

    return ""
