from fastapi import FastAPI, HTTPException, Query

from app.config import (
    APP_NAME,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    OLLAMA_PROVIDER,
    OLLAMA_PROVIDER_CONFIGS,
    OLLAMA_PROVIDERS,
    QDRANT_COLLECTION,
)
from app.rag_service import query_documents, reindex_documents


app = FastAPI(title=APP_NAME, version="1.0.0")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "llm_provider": OLLAMA_PROVIDER,
        "llm_providers": OLLAMA_PROVIDERS,
        "llm_model": OLLAMA_LLM_MODEL,
        "llm_models": OLLAMA_PROVIDER_CONFIGS[OLLAMA_PROVIDER]["models"],
        "llm_base_url": OLLAMA_PROVIDER_CONFIGS[OLLAMA_PROVIDER]["base_url"],
        "embed_model": OLLAMA_EMBED_MODEL,
        "collection": QDRANT_COLLECTION,
    }


@app.get("/ask")
def ask(
    query: str = Query(..., min_length=1),
    llm_model: str | None = Query(default=None),
    llm_provider: str | None = Query(default=None),
) -> dict[str, object]:
    try:
        result = query_documents(query, llm_model=llm_model, llm_provider=llm_provider)
        return {
            "answer": result.answer,
            "sources": [
                {
                    "filename": source.filename,
                    "path": source.path,
                    "score": source.score,
                    "excerpt": source.excerpt,
                }
                for source in result.sources
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/reindex")
def reindex() -> dict[str, int | str]:
    try:
        return reindex_documents()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
