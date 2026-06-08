# POC RAG local avec LlamaIndex, Qdrant et Ollama

Ce depot contient un POC local d'assistant documentaire capable d'indexer des fichiers PDF, DOCX et TXT, puis de repondre en francais avec citations de sources.

Le POC repose sur :

- `LlamaIndex` pour l'orchestration RAG ;
- `Qdrant` pour la recherche vectorielle ;
- `Ollama` local pour le LLM et les embeddings ;
- `FastAPI` pour l'API ;
- `Streamlit` pour l'interface locale ;
- `PyMuPDF`, `EasyOCR` et `python-docx` pour l'extraction documentaire.

## Prerequis

- Python 3.10+
- Docker et Docker Compose
- Ollama installe localement
- Pour les PDF scannes : `EasyOCR` via `pip`, et `poppler-utils`

## Installation d'Ollama

Installer Ollama puis telecharger au minimum les modeles suivants :

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

Verifier qu'Ollama tourne localement :

```bash
ollama list
```

Par defaut, le projet cible `http://localhost:11434`.

## Configuration

Copier le fichier d'exemple :

```bash
cp .env.example .env
```

Variables principales :

- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_LLM_MODEL=qwen2.5:7b`
- `OLLAMA_EMBED_MODEL=nomic-embed-text`
- `QDRANT_URL=http://localhost:6333`
- `QDRANT_COLLECTION=documents_local_rag`
- `DATA_DIR=./data/documents`

## Lancer Qdrant

Le `docker-compose.yml` racine lance Qdrant en local :

```bash
docker compose up -d qdrant
```

Verification :

```bash
curl http://localhost:6333/healthz
```

## Installer les dependances Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

Au premier lancement OCR, `EasyOCR` peut telecharger ses modeles localement.

## Ajouter des documents

Deposez vos fichiers dans `data/documents/`.

Le dossier versionne reste vide par defaut via `.gitkeep`. Les documents reels ne sont pas commites.

Types supportes :

- PDF texte ;
- PDF scannes avec OCR ;
- DOCX ;
- TXT.

## Indexer les documents

```bash
python3 -m app.ingest
```

La reindexation reconstruit la collection Qdrant du POC.

## Lancer l'application

### Interface Streamlit

```bash
streamlit run app/streamlit_app.py
```

L'interface permet :

- de poser une question ;
- de voir la reponse generee ;
- de consulter les sources citees ;
- de relancer la reindexation.

### API FastAPI

```bash
uvicorn app.rag_api:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints utiles :

- `GET /health`
- `GET /ask?query=...`
- `POST /reindex`

Exemple :

```bash
curl "http://localhost:8000/ask?query=Quels%20elements%20ressortent%20du%20document%20indexe%20%3F"
```

## Exemple de test rapide

1. Placer un PDF ou DOCX dans `data/documents/`.
2. Executer `python3 -m app.ingest`.
3. Lancer `streamlit run app/streamlit_app.py`.
4. Poser une question en francais relative au document.
5. Verifier que la reponse contient des sources avec nom de fichier et extrait.

## Documentation projet

- Analyse initiale : [docs/poc-rag-analysis.md](docs/poc-rag-analysis.md)
- Plan d'implementation : [docs/poc-rag-implementation-plan.md](docs/poc-rag-implementation-plan.md)

## Limites actuelles du POC

- pas d'authentification ni de gestion des droits ;
- pas d'indexation incrementale ;
- pas de deduplication documentaire ;
- pas de pipeline de tests automatise ;
- performance et qualite dependantes des modeles Ollama et de la machine locale.
