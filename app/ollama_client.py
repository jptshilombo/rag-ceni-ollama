from typing import Any

import requests

from app.config import OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL, OLLAMA_REQUEST_TIMEOUT
from app.rag_service import _get_provider_config


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json"}


def embed(text: str) -> list[float]:
    provider_config = _get_provider_config("local")
    base_url = str(provider_config["base_url"])
    headers = {**_headers(), **dict(provider_config.get("headers", {}) or {})}
    verify = bool(provider_config.get("verify", True))
    response = requests.post(
        f"{base_url}/api/embeddings",
        headers=headers,
        json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=OLLAMA_REQUEST_TIMEOUT,
        verify=verify,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    # Native Ollama Cloud format: {"embeddings": [[...]]}
    if "embeddings" in data and data["embeddings"]:
        return data["embeddings"][0]

    # OpenAI-compatible format: {"data": [{"embedding": [...]}]}
    if "data" in data and data["data"]:
        return data["data"][0]["embedding"]

    # Legacy single-vector format
    if "embedding" in data:
        return data["embedding"]

    raise RuntimeError("Unexpected embedding response format from Ollama.")


def ask_llm(prompt: str, llm_model: str | None = None, llm_provider: str | None = None) -> str:
    provider_config = _get_provider_config(llm_provider)
    base_url = str(provider_config["base_url"])
    headers = {**_headers(), **dict(provider_config.get("headers", {}) or {})}
    verify = bool(provider_config.get("verify", True))
    response = requests.post(
        f"{base_url}/api/generate",
        headers=headers,
        json={
            "model": llm_model or OLLAMA_LLM_MODEL,
            "prompt": prompt,
            "temperature": 0.2,
            "stream": False,
        },
        timeout=OLLAMA_REQUEST_TIMEOUT,
        verify=verify,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return str(data["response"]).strip()
