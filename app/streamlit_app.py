from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_NAME, DATA_DIR, OLLAMA_EMBED_MODEL, OLLAMA_LLM_MODEL, QDRANT_COLLECTION
from app.rag_service import query_documents, reindex_documents


st.set_page_config(page_title=APP_NAME, page_icon=":books:", layout="wide")
st.title(APP_NAME)
st.caption("POC local RAG base sur LlamaIndex, Qdrant et Ollama.")

with st.sidebar:
    st.subheader("Configuration")
    st.write(f"Documents: `{DATA_DIR}`")
    st.write(f"Collection Qdrant: `{QDRANT_COLLECTION}`")
    st.write(f"LLM Ollama: `{OLLAMA_LLM_MODEL}`")
    st.write(f"Embeddings Ollama: `{OLLAMA_EMBED_MODEL}`")

    if st.button("Reindexer les documents", use_container_width=True):
        with st.spinner("Reindexation en cours..."):
            try:
                result = reindex_documents()
                st.success(
                    f"Index reconstruit : {result['documents']} document(s), {result['chunks']} chunk(s)."
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
                result = query_documents(question.strip())
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
