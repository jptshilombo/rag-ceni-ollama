from typing import Any

import requests

from config import MODEL_EMBED, MODEL_LLM, MODEL_LLM_HERMES, OLLAMA_API_KEY


OLLAMA_BASE_URL = "https://api.ollama.com/v1"
REQUEST_TIMEOUT_SECONDS = 120


def _headers() -> dict[str, str]:
    if not OLLAMA_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY is required.")
    return {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }


def embed(text: str) -> list[float]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/embeddings",
        headers=_headers(),
        json={"model": MODEL_EMBED, "input": text},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    if "embedding" in data:
        return data["embedding"]

    if "data" in data and data["data"]:
        return data["data"][0]["embedding"]

    raise RuntimeError("Unexpected embedding response format from Ollama Cloud.")


def ask_llm(prompt: str, model: str = "qwen") -> str:
    selected_model = MODEL_LLM_HERMES if model == "hermes" else MODEL_LLM
    response = requests.post(
        f"{OLLAMA_BASE_URL}/chat/completions",
        headers=_headers(),
        json={
            "model": selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant RAG pour des archives electorales CENI. "
                        "Reponds de facon factuelle et cite les limites du contexte."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data["choices"][0]["message"]["content"]
