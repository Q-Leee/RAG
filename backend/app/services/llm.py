import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def chat(
    messages: list[dict],
    *,
    timeout: float = 180.0,
    temperature: float | None = None,
) -> str | None:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    temp = settings.ollama_temperature if temperature is None else temperature
    payload = {
        "model": settings.ollama_chat_model,
        "stream": False,
        "messages": messages,
        "options": {"temperature": temp},
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
            if r.status_code >= 400:
                logger.error("Ollama chat %s: %s", r.status_code, r.text[:500])
                return None
            data = r.json()
            msg = (data.get("message") or {}).get("content")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
    except Exception:
        logger.exception("Ollama chat failed")
    return None


def extract_json_block(text: str) -> dict | None:
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None
