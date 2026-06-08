from __future__ import annotations

import json
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
    INDEX_METADATA_PATH,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    OLLAMA_PROVIDER,
    OLLAMA_PROVIDER_CONFIGS,
    OLLAMA_PROVIDERS,
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


def _get_provider_config(provider: str | None = None) -> dict[str, Any]:
    selected_provider = (provider or OLLAMA_PROVIDER).strip().lower()
    if selected_provider not in OLLAMA_PROVIDERS:
        raise RuntimeError(
            f"Provider Ollama non autorise: `{selected_provider}`. Providers autorises: {', '.join(OLLAMA_PROVIDERS)}."
        )
    provider_config = OLLAMA_PROVIDER_CONFIGS[selected_provider]
    if selected_provider == "cloud" and not provider_config.get("headers"):
        raise RuntimeError(
            "Le provider Ollama Cloud requiert `OLLAMA_API_KEY` dans la configuration."
        )
    return provider_config


def _load_index_metadata() -> dict[str, Any] | None:
    if not INDEX_METADATA_PATH.exists():
        return None
    return json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))


def _save_index_metadata(vector_size: int) -> None:
    INDEX_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_METADATA_PATH.write_text(
        json.dumps(
            {
                "collection": QDRANT_COLLECTION,
                "embedding_model": OLLAMA_EMBED_MODEL,
                "vector_size": vector_size,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _validate_embedding_contract(vector_size: int | None = None) -> None:
    metadata = _load_index_metadata()
    if metadata is None:
        raise RuntimeError(
            "Configuration d'embeddings non verifiee. Lancez une reindexation complete Qdrant avec `bge-m3`."
        )

    indexed_model = str(metadata.get("embedding_model", "")).strip()
    if indexed_model != OLLAMA_EMBED_MODEL:
        raise RuntimeError(
            "Le modele d'embeddings configure ne correspond pas a l'index Qdrant. "
            "Une reindexation complete est requise."
        )

    indexed_collection = str(metadata.get("collection", "")).strip()
    if indexed_collection != QDRANT_COLLECTION:
        raise RuntimeError(
            "La collection Qdrant ne correspond pas aux metadonnees d'index locales. "
            "Une reindexation complete est requise."
        )

    if vector_size is not None and int(metadata.get("vector_size", -1)) != vector_size:
        raise RuntimeError(
            "La dimension des embeddings ne correspond pas a l'index Qdrant. "
            "Une reindexation complete est requise."
        )


def get_embed_model() -> OllamaEmbedding:
    base_url = str(_get_provider_config("local")["base_url"])
    return OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=base_url,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )


def get_llm(model_name: str | None = None, provider: str | None = None) -> Ollama:
    provider_config = _get_provider_config(provider)
    allowed_models = [str(model) for model in provider_config["models"]]
    headers = dict(provider_config.get("headers", {}) or {})
    selected_model = (model_name or OLLAMA_LLM_MODEL).strip()
    if selected_model not in allowed_models:
        raise RuntimeError(
            f"Modele LLM non autorise pour `{provider or OLLAMA_PROVIDER}`: `{selected_model}`. "
            f"Modeles autorises: {', '.join(allowed_models)}."
        )
    return Ollama(
        model=selected_model,
        base_url=str(provider_config["base_url"]),
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
        headers=headers,
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
        f"Tu es {APP_NAME}, un assistant RAG documentaire.\n"
        "Reponds uniquement en francais.\n"
        "Utilise exclusivement les extraits de contexte fournis.\n"
        "N'ajoute aucun fait externe, aucune supposition et aucune interpretation non appuyee par le contexte.\n"
        "Si le contexte est insuffisant, contradictoire ou absent, dis-le explicitement.\n"
        "Si plusieurs extraits convergent, fais une synthese breve et factuelle.\n"
        "Cite la ou les sources a la fin de chaque point important avec le format [Source n].\n"
        "Ne cite jamais une source que tu n'as pas utilisee.\n"
        "Ne mentionne pas de score de similarite.\n"
        "Garde la reponse concise et utile.\n\n"
        "Format de sortie attendu:\n"
        "- Reponse: 2 a 6 phrases ou points courts.\n"
        "- Si l'information manque: commence par `Information insuffisante dans les sources fournies.`\n"
        "- Termine par une ligne `Sources utilisees: [Source x], [Source y]`.\n\n"
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
    _save_index_metadata(len(probe_vector))

    return {
        "status": "indexed",
        "documents": len(documents),
        "chunks": len(nodes),
        "collection": QDRANT_COLLECTION,
        "embedding_model": OLLAMA_EMBED_MODEL,
    }


def query_documents(
    question: str,
    llm_model: str | None = None,
    llm_provider: str | None = None,
) -> QueryResult:
    embed_model = get_embed_model()
    probe_vector = embed_model.get_text_embedding("dimension probe")
    _validate_embedding_contract(len(probe_vector))
    client = get_qdrant_client()
    _ensure_collection(client, len(probe_vector))

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

    response = get_llm(llm_model, provider=llm_provider).complete(_build_prompt(question, sources))
    return QueryResult(answer=response.text.strip(), sources=sources)
