# Plan d'implementation du POC RAG local

## Architecture cible

- `Streamlit` pour l'interface locale de demonstration ;
- `FastAPI` conserve comme point d'entree API ;
- `LlamaIndex` pour l'ingestion, le chunking, le retrieval et l'orchestration RAG ;
- `Qdrant` comme base vectorielle locale ;
- `Ollama` local pour :
  - generation (`qwen2.5:7b` par defaut) ;
  - embeddings (`nomic-embed-text` par defaut) ;
- extraction documentaire via :
  - `PyMuPDF` pour PDF texte ;
  - `Tesseract + pdf2image` pour PDF scannes ;
  - `python-docx` pour DOCX.

## Arborescence proposee

```text
app/
  __init__.py
  config.py
  document_loader.py
  ingest.py
  ocr_utils.py
  rag_api.py
  rag_service.py
  streamlit_app.py
  requirements.txt
data/
  documents/
    .gitkeep
docs/
  poc-rag-analysis.md
  poc-rag-implementation-plan.md
docker-compose.yml
README.md
.env.example
```

## Etapes d'installation locale

1. Installer Python 3.10+ et Ollama.
2. Telecharger les modeles Ollama :
   - `ollama pull qwen2.5:7b`
   - `ollama pull nomic-embed-text`
3. Copier `.env.example` vers `.env`.
4. Lancer Qdrant avec `docker compose up -d qdrant`.
5. Installer les dependances Python avec `pip install -r app/requirements.txt`.
6. Placer des PDF/DOCX dans `data/documents/`.
7. Indexer avec `python3 -m app.ingest`.
8. Lancer l'interface :
   - API : `uvicorn app.rag_api:app --reload`
   - UI : `streamlit run app/streamlit_app.py`

## Choix techniques justifies

- `LlamaIndex` simplifie l'integration avec Qdrant et Ollama tout en gardant une architecture extensible.
- `Qdrant` est deja present dans le projet et convient bien a un POC local.
- `Streamlit` permet une UI rapide sans introduire un frontend lourd.
- la conservation de `FastAPI` facilite une evolution future vers une architecture BFF/API.
- la lecture documentaire custom garde le support OCR deja existant, plus maitrise que des loaders generiques.

## Risques et limites

- qualite variable sur les PDF scannes selon l'OCR et la qualite des documents ;
- performance dependante de la machine locale et des modeles Ollama charges ;
- absence de securisation, multi-utilisateur, audit et cloisonnement documentaire ;
- reindexation complete, sans indexation incrementale ni deduplication avancee ;
- absence de pipeline de tests fonctionnels automatises du POC.

## Criteres d'acceptation du POC

- Qdrant demarre localement via Docker Compose ;
- Ollama local est utilise pour le LLM et les embeddings ;
- un document depose dans `data/documents/` peut etre indexe ;
- une question peut etre posee via API ou Streamlit ;
- la reponse est en francais et expose les sources utilisees ;
- le README permet a un autre developpeur de relancer le POC.
