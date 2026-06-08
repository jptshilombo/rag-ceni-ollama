from typing import Any

import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL, OLLAMA_REQUEST_TIMEOUT


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json"}


def embed(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        headers=_headers(),
        json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=OLLAMA_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    if "embedding" not in data:
        raise RuntimeError("Unexpected embedding response format from Ollama.")
    return data["embedding"]


def ask_llm(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        headers=_headers(),
        json={
            "model": OLLAMA_LLM_MODEL,
            "prompt": prompt,
            "temperature": 0.2,
            "stream": False,
        },
        timeout=OLLAMA_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return str(data["response"]).strip()
