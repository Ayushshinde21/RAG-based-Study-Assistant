
import os
from typing import Any

from langchain_groq import ChatGroq

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def get_groq_llm(*, response_mime_type: str | None = None) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Add your Groq API key to .env."
        )

    config: dict[str, Any] = {
        "model": MODEL_NAME,
        "api_key": api_key,
        "temperature": 0.2,
        "max_retries": 2,
        "timeout": 60,
        "reasoning_format": "hidden",
    }

    if response_mime_type:
        if response_mime_type != "application/json":
            raise ValueError(
                "Groq response mode supports application/json here."
            )

        config["streaming"] = False
        config["model_kwargs"] = {
            "response_format": {"type": "json_object"}
        }

    return ChatGroq(**config)


def response_text(message: Any) -> str:
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


def stream_chunk_text(message: Any) -> str:
    """Extract text from one streaming chunk without trimming its whitespace.

    Leading spaces are meaningful in streamed language-model output: stripping
    each chunk separately joins words that arrived in adjacent chunks.
    """
    if isinstance(message, str):
        return message

    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content

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
        return "".join(text_parts)

    text_value = getattr(message, "text", None)
    return text_value if isinstance(text_value, str) else ""
