from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import (
    APP_NAME,
    DATA_DIR,
    OLLAMA_EMBED_MODEL,
    OLLAMA_LLM_MODEL,
    OLLAMA_PROVIDER,
    OLLAMA_PROVIDER_CONFIGS,
    OLLAMA_PROVIDERS,
    QDRANT_COLLECTION,
)
from app.rag_service import query_documents, reindex_documents


st.set_page_config(page_title=APP_NAME, page_icon=":books:", layout="wide")
st.title(APP_NAME)
st.caption("POC local RAG base sur LlamaIndex, Qdrant et Ollama.")

with st.sidebar:
    st.subheader("Configuration")
    st.write(f"Documents: `{DATA_DIR}`")
    st.write(f"Collection Qdrant: `{QDRANT_COLLECTION}`")
    st.write(f"Embeddings Ollama: `{OLLAMA_EMBED_MODEL}`")
    selected_provider = st.selectbox(
        "Provider Ollama",
        options=OLLAMA_PROVIDERS,
        index=OLLAMA_PROVIDERS.index(OLLAMA_PROVIDER),
    )
    provider_models = [str(model) for model in OLLAMA_PROVIDER_CONFIGS[selected_provider]["models"]]
    default_llm = OLLAMA_LLM_MODEL if OLLAMA_LLM_MODEL in provider_models else provider_models[0]
    selected_llm = st.selectbox(
        "LLM Ollama",
        options=provider_models,
        index=provider_models.index(default_llm),
    )
    st.write(f"Endpoint actif: `{OLLAMA_PROVIDER_CONFIGS[selected_provider]['base_url']}`")
    st.caption("Le changement d'embeddings n'est pas autorise sans reindexation complete.")

    if st.button("Reindexer les documents", use_container_width=True):
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def update_progress(step: str, current: int, total: int, message: str) -> None:
            if step == "load":
                base_percent = 0
                step_percent = 10
            elif step == "split":
                base_percent = 10
                step_percent = 10
            elif step == "setup":
                base_percent = 20
                step_percent = 10
            elif step == "embed":
                base_percent = 30
                step_percent = 65
            else:
                base_percent = 95
                step_percent = 5

            ratio = current / total if total else 0
            progress_bar.progress(min(100, base_percent + int(ratio * step_percent)))
            progress_text.write(message)

        try:
            result = reindex_documents(progress_callback=update_progress)
            progress_bar.progress(100)
            progress_text.write("Indexation terminee.")
            st.success(
                f"Index reconstruit : {result['documents']} document(s), {result['chunks']} chunk(s), embeddings `{result['embedding_model']}`."
            )
        except Exception as exc:
            st.error(str(exc))

question = st.text_area(
    "Question",
    placeholder="Exemple : Quels sont les points cles mentionnes dans les documents indexes ?",
    height=120,
)

if st.button("Poser la question", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Saisissez une question.")
    else:
        with st.spinner("Recherche et generation en cours..."):
            try:
                result = query_documents(
                    question.strip(),
                    llm_model=selected_llm,
                    llm_provider=selected_provider,
                )
            except Exception as exc:
                st.error(str(exc))
            else:
                st.subheader("Reponse")
                st.write(result.answer)

                st.subheader("Sources")
                if not result.sources:
                    st.info("Aucune source pertinente trouvee.")
                else:
                    for index, source in enumerate(result.sources, start=1):
                        score_label = f"{source.score:.4f}" if source.score is not None else "n/a"
                        st.markdown(
                            f"**{index}. {source.filename}**  \n"
                            f"`{source.path}`  \n"
                            f"Score: `{score_label}`"
                        )
                        st.caption(source.excerpt)
