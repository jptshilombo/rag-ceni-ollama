from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from qdrant_client import QdrantClient

from config import QDRANT_URL
from ingest import COLLECTION_NAME
from ollama_client import ask_llm, embed


app = FastAPI(title="RAG CENI Ollama Cloud", version="1.0.0")
qdrant = QdrantClient(url=QDRANT_URL)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def build_prompt(query: str, contexts: list[str]) -> str:
    context = "\n\n---\n\n".join(contexts)
    return f"""
Tu reponds a une question sur des archives CENI.

Instruction stricte:
- Reponds uniquement a partir des documents fournis dans le contexte.
- Si le contexte ne permet pas de repondre, dis clairement que les archives fournies ne contiennent pas l'information.
- Mentionne que la reponse provient d'archives CENI.

Contexte:
{context}

Question:
{query}
""".strip()


@app.get("/ask")
def ask(
    query: str = Query(..., min_length=1),
    model: Literal["qwen", "hermes"] = "qwen",
) -> dict[str, object]:
    try:
        query_vector = embed(query)
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=5,
        )
        contexts = [str(result.payload.get("text", "")) for result in results if result.payload]
        sources = [
            {
                "filename": result.payload.get("filename"),
                "type_document": result.payload.get("type_document"),
                "cycle_electoral": result.payload.get("cycle_electoral"),
                "score": result.score,
            }
            for result in results
            if result.payload
        ]
        answer = ask_llm(build_prompt(query, contexts), model=model)
        return {"answer": answer, "sources": sources}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
