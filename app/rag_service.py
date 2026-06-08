from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import (
    APP_NAME,
    DATA_DIR,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    OLLAMA_REQUEST_TIMEOUT,
    QDRANT_COLLECTION,
    QDRANT_URL,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_TOP_K,
)
from app.document_loader import load_documents


@dataclass
class SourceSnippet:
    filename: str
    path: str
    score: float | None
    excerpt: str


@dataclass
class QueryResult:
    answer: str
    sources: list[SourceSnippet]


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def get_embed_model() -> OllamaEmbedding:
    return OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )


def get_llm() -> Ollama:
    return Ollama(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )


def _ensure_collection(client: QdrantClient, vector_size: int, recreate: bool = False) -> None:
    existing = {collection.name for collection in client.get_collections().collections}
    if recreate and QDRANT_COLLECTION in existing:
        client.delete_collection(QDRANT_COLLECTION)
        existing.remove(QDRANT_COLLECTION)

    if QDRANT_COLLECTION in existing:
        return

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def _get_vector_store(client: QdrantClient) -> QdrantVectorStore:
    return QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION)


def _get_text_from_result(result: Any) -> str:
    node = getattr(result, "node", result)
    return node.get_content().strip()


def _get_metadata_from_result(result: Any) -> dict[str, Any]:
    node = getattr(result, "node", result)
    return dict(getattr(node, "metadata", {}) or {})


def _build_prompt(question: str, sources: list[SourceSnippet]) -> str:
    context_blocks = []
    for index, source in enumerate(sources, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"Source {index}: {source.filename}",
                    f"Chemin: {source.path}",
                    f"Extrait: {source.excerpt}",
                ]
            )
        )

    context = "\n\n".join(context_blocks) if context_blocks else "Aucun contexte disponible."
    return (
        f"Tu es {APP_NAME}. Reponds en francais, de facon factuelle et concise.\n"
        "Base-toi uniquement sur les extraits fournis.\n"
        "Si l'information n'est pas presente, dis-le clairement.\n"
        "Quand tu t'appuies sur plusieurs passages, fais une synthese courte.\n\n"
        f"Question:\n{question}\n\n"
        f"Contexte:\n{context}\n\n"
        "Reponse attendue:"
    )


def reindex_documents() -> dict[str, int | str]:
    documents = load_documents(DATA_DIR)
    if not documents:
        raise RuntimeError(
            f"Aucun document supporte trouve dans {DATA_DIR}. Ajoutez des PDF, DOCX ou TXT."
        )

    splitter = SentenceSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    embed_model = get_embed_model()
    probe_vector = embed_model.get_text_embedding("dimension probe")
    client = get_qdrant_client()
    _ensure_collection(client, len(probe_vector), recreate=True)

    storage_context = StorageContext.from_defaults(vector_store=_get_vector_store(client))
    VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)

    return {
        "status": "indexed",
        "documents": len(documents),
        "chunks": len(nodes),
        "collection": QDRANT_COLLECTION,
    }


def query_documents(question: str) -> QueryResult:
    embed_model = get_embed_model()
    client = get_qdrant_client()
    _ensure_collection(client, len(embed_model.get_text_embedding("dimension probe")))

    index = VectorStoreIndex.from_vector_store(
        vector_store=_get_vector_store(client),
        embed_model=embed_model,
    )
    retriever = index.as_retriever(similarity_top_k=RAG_TOP_K)
    results = retriever.retrieve(question)

    sources: list[SourceSnippet] = []
    for result in results:
        text = _get_text_from_result(result)
        metadata = _get_metadata_from_result(result)
        sources.append(
            SourceSnippet(
                filename=str(metadata.get("filename", "inconnu")),
                path=str(metadata.get("path", "")),
                score=getattr(result, "score", None),
                excerpt=text[:500],
            )
        )

    if not sources:
        return QueryResult(
            answer="Je ne trouve pas de passage pertinent dans l'index local pour repondre a cette question.",
            sources=[],
        )

    response = get_llm().complete(_build_prompt(question, sources))
    return QueryResult(answer=response.text.strip(), sources=sources)
