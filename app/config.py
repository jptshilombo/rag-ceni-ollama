import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

APP_NAME: str = os.getenv("APP_NAME", "Assistant documentaire local")
ENV: str = os.getenv("ENV", "local")

OLLAMA_PROVIDER: str = os.getenv("OLLAMA_PROVIDER", "local").strip().lower()
OLLAMA_LOCAL_BASE_URL: str = os.getenv("OLLAMA_LOCAL_BASE_URL", "http://localhost:11434")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", OLLAMA_LOCAL_BASE_URL)
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_CLOUD_SSL_VERIFY: bool = os.getenv("OLLAMA_CLOUD_SSL_VERIFY", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
OLLAMA_LOCAL_LLM_MODELS_RAW: str = os.getenv("OLLAMA_LOCAL_LLM_MODELS", os.getenv("OLLAMA_LLM_MODELS", OLLAMA_LLM_MODEL))
OLLAMA_CLOUD_LLM_MODELS_RAW: str = os.getenv("OLLAMA_CLOUD_LLM_MODELS", OLLAMA_LLM_MODEL)


def _normalize_ollama_host(raw_url: str) -> str:
    base_url = raw_url.rstrip("/")
    if base_url.endswith("/api"):
        return base_url[:-4]
    return base_url


def _parse_models(raw_value: str) -> list[str]:
    return [model.strip() for model in raw_value.split(",") if model.strip()]


OLLAMA_CLOUD_BASE_URL: str = _normalize_ollama_host(
    os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com/api")
)
OLLAMA_LOCAL_LLM_MODELS: list[str] = _parse_models(OLLAMA_LOCAL_LLM_MODELS_RAW)
OLLAMA_CLOUD_LLM_MODELS: list[str] = _parse_models(OLLAMA_CLOUD_LLM_MODELS_RAW)
if not OLLAMA_LOCAL_LLM_MODELS:
    OLLAMA_LOCAL_LLM_MODELS = [OLLAMA_LLM_MODEL]
if not OLLAMA_CLOUD_LLM_MODELS:
    OLLAMA_CLOUD_LLM_MODELS = [OLLAMA_LLM_MODEL]

OLLAMA_PROVIDERS: list[str] = ["local", "cloud"]
if OLLAMA_PROVIDER not in OLLAMA_PROVIDERS:
    OLLAMA_PROVIDER = "local"

OLLAMA_PROVIDER_CONFIGS: dict[str, dict[str, object]] = {
    "local": {
        "base_url": OLLAMA_LOCAL_BASE_URL,
        "models": OLLAMA_LOCAL_LLM_MODELS,
        "headers": {},
        "verify": True,
    },
    "cloud": {
        "base_url": OLLAMA_CLOUD_BASE_URL,
        "models": OLLAMA_CLOUD_LLM_MODELS,
        "headers": (
            {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
            if OLLAMA_API_KEY
            else {}
        ),
        "verify": OLLAMA_CLOUD_SSL_VERIFY,
    },
}

OLLAMA_LLM_MODELS: list[str] = list(OLLAMA_PROVIDER_CONFIGS[OLLAMA_PROVIDER]["models"])
if OLLAMA_LLM_MODEL not in OLLAMA_LLM_MODELS:
    OLLAMA_LLM_MODELS.insert(0, OLLAMA_LLM_MODEL)

OLLAMA_EMBED_MODEL: str = "bge-m3"
OLLAMA_REQUEST_TIMEOUT: float = float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "120"))

QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "documents_local_rag")

OCR_LANG: str = os.getenv("OCR_LANG", "fra")

RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "900"))
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))

_data_dir = Path(os.getenv("DATA_DIR", "data/documents"))
if not _data_dir.is_absolute():
    _data_dir = BASE_DIR / _data_dir
DATA_DIR: Path = _data_dir.resolve()

INDEX_METADATA_PATH: Path = (BASE_DIR / "data" / "index_metadata.json").resolve()
