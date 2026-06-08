import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

APP_NAME: str = os.getenv("APP_NAME", "Assistant documentaire local")
ENV: str = os.getenv("ENV", "local")

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
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
