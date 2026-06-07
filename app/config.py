import os

from dotenv import load_dotenv


load_dotenv()

OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
MODEL_LLM: str = os.getenv("MODEL_LLM", "qwen2.5:7b")
MODEL_LLM_HERMES: str = os.getenv("MODEL_LLM_HERMES", "hermes-3:8b")
MODEL_EMBED: str = os.getenv("MODEL_EMBED", "nomic-embed-text")
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
OCR_LANG: str = os.getenv("OCR_LANG", "fra")
ENV: str = os.getenv("ENV", "local")
