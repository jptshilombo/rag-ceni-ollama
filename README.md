# RAG CENI Ollama Cloud

## Introduction

Ce projet fournit un RAG complet pour documents CENI : PV, lois, rapports et archives electorales. Il combine Ollama Cloud pour le LLM et les embeddings, Qdrant pour la recherche vectorielle, FastAPI comme orchestrateur et une couche OCR pour les PDF scannes.

Deux variantes de modele sont configurees : Qwen2.5 et Hermes.

## Prerequis

- Docker
- Docker Compose
- Cle API Ollama Cloud
- Pour une ingestion hors Docker : Python 3.10, Tesseract OCR et Poppler

## Configuration

```bash
cp .env.example .env
```

Renseignez au minimum :

```bash
OLLAMA_API_KEY=<votre_cle_ollama_cloud>
```

Variables principales :

- `MODEL_LLM=qwen2.5:7b`
- `MODEL_LLM_HERMES=hermes-3:8b`
- `MODEL_EMBED=nomic-embed-text`
- `QDRANT_URL=http://qdrant:6333`
- `OCR_LANG=fra`
- `ENV=local`

## Lancement en local

Demarrer Qdrant et l'API :

```bash
docker compose -f docker/docker-compose.local.yml up -d --build
```

Placez vos documents dans `data/`, puis lancez l'ingestion :

```bash
docker compose -f docker/docker-compose.local.yml run --rm api python ingest.py
```

Interroger l'API :

```bash
curl "http://localhost:8000/ask?query=Quels%20documents%20mentionnent%20les%20resultats%20provisoires%20%3F"
```

Verification :

```bash
curl "http://localhost:8000/health"
```

## Lancement sur AWS

Le deploiement AWS cible une instance EC2 sans GPU, car les modeles sont appeles via Ollama Cloud.

Resume :

```bash
git clone <URL_DU_REPO> rag-ceni-ollama
cd rag-ceni-ollama
cp .env.example .env
docker compose -f docker/docker-compose.aws.yml up -d --build
docker compose -f docker/docker-compose.aws.yml run --rm api python ingest.py
```

Voir le guide detaille : `infra/aws_ec2_setup.md`.

## Utilisation des modeles

Modele Qwen par defaut :

```bash
curl "http://localhost:8000/ask?query=Votre%20question&model=qwen"
```

Modele Hermes :

```bash
curl "http://localhost:8000/ask?query=Votre%20question&model=hermes"
```

## Specificites CENI

L'ingestion detecte automatiquement :

- PDF texte via PyMuPDF.
- PDF scannes via OCR Tesseract.
- TXT en lecture directe.
- DOCX via `python-docx`.

Les chunks envoyes dans Qdrant incluent les metadonnees suivantes :

- `filename`
- `path`
- `type_document` : `pv`, `loi`, `rapport` ou `autre`
- `cycle_electoral` : annee detectee dans le nom du fichier
- `chunk_index`
- `text`

Le prompt RAG impose de repondre uniquement a partir du contexte extrait des archives CENI.

## Evolutions possibles

- Interface web Streamlit.
- Authentification API.
- Reverse proxy Nginx ou ALB AWS avec HTTPS.
- Monitoring applicatif et metriques d'usage.
- Stockage S3 pour les documents sources.
- Indexation incrementale avec suivi des hash de fichiers.
