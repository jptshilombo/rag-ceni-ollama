from fastapi import FastAPI, HTTPException, Query

from app.config import APP_NAME, OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL, QDRANT_COLLECTION
from app.rag_service import query_documents, reindex_documents


app = FastAPI(title=APP_NAME, version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "llm_model": OLLAMA_LLM_MODEL,
        "embed_model": OLLAMA_EMBED_MODEL,
        "collection": QDRANT_COLLECTION,
    }


@app.get("/ask")
def ask(query: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        result = query_documents(query)
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
