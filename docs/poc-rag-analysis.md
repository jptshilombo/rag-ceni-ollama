# Analyse du projet existant

## Etat actuel du projet

Le depot contient deja une base Python orientee RAG, avec les elements suivants :

- un backend FastAPI minimal dans `app/rag_api.py` ;
- une ingestion documentaire custom dans `app/ingest.py` ;
- une integration Qdrant existante ;
- une extraction PDF/DOCX/TXT avec OCR pour les PDF scannes ;
- une configuration Docker existante dans `docker/`.

Constats principaux :

- la logique actuelle utilise une API Ollama Cloud via `requests` et une cle API ;
- LlamaIndex n'est pas utilise ;
- il n'existe pas d'interface web utilisateur ;
- les documents etaient attendus dans `data/` sans sous-dossier dedie ;
- il n'y a pas de tests automatises ;
- la documentation est orientee cloud et non POC local.

## Opportunites de reutilisation

Les briques reutilisables sont :

- `app/ocr_utils.py` pour l'extraction PDF texte ou OCR ;
- la lecture DOCX existante ;
- la presence de Qdrant dans l'architecture ;
- la structure Python simple, facile a refondre sans gros impact ;
- les fichiers Docker deja presents, utiles comme base pour une execution locale.

## Ecarts par rapport au POC cible

Ecarts identifies :

- absence de LlamaIndex pour structurer ingestion, chunking et retrieval ;
- dependance actuelle a Ollama Cloud, non conforme a l'exigence locale ;
- absence d'interface Streamlit ;
- absence de dossier `data/documents` dedie ;
- absence de `docker-compose.yml` racine standardise pour Qdrant ;
- absence de README oriente relance locale du POC ;
- pas de mecanisme clair de reindexation expose a l'utilisateur ;
- pas de format de reponse avec extraits/sources suffisamment explicites.

## Plan d'implementation recommande

1. Conserver Python, Qdrant et les utilitaires OCR/documents deja presents.
2. Basculer la couche RAG sur LlamaIndex avec Ollama local pour LLM et embeddings.
3. Introduire un service central reutilisable par FastAPI, Streamlit et le script d'ingestion.
4. Normaliser la configuration via `.env.example`, `docker-compose.yml` et `data/documents/`.
5. Ajouter une interface Streamlit simple pour question/reponse/sources/reindexation.
6. Mettre a jour le README pour une relance locale complete et reproductible.
