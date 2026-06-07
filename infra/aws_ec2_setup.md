# Deploiement AWS EC2

## Instance recommandee

Pour un POC RAG CENI avec Qdrant, OCR et API FastAPI :

- `t3.large` : point de depart acceptable pour un faible volume.
- `t3.xlarge` : recommande si plusieurs PDF scannes ou plusieurs utilisateurs sont prevus.

Ollama Cloud fournit le LLM et les embeddings, donc l'instance EC2 n'a pas besoin de GPU.

## Ports a ouvrir

- `22` : SSH, limite a votre IP d'administration.
- `80` / `443` : reverse proxy HTTP/HTTPS si Nginx, ALB ou Traefik est ajoute.
- `8000` : API FastAPI pour POC uniquement, limite a des IPs precises.

Qdrant (`6333`) doit rester interne a l'instance ou au reseau prive.

## Installation

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Reconnectez-vous apres l'ajout au groupe `docker`.

## Lancement

```bash
git clone <URL_DU_REPO> rag-ceni-ollama
cd rag-ceni-ollama
cp .env.example .env
```

Renseignez `OLLAMA_API_KEY` dans `.env`, puis demarrez :

```bash
docker compose -f docker/docker-compose.aws.yml up -d --build
```

## Ingestion des documents

Placez les PDF, TXT ou DOCX dans `data/`, puis lancez l'ingestion depuis le conteneur API :

```bash
docker compose -f docker/docker-compose.aws.yml run --rm api python ingest.py
```

Alternative locale sur l'instance, si Python et Tesseract sont installes :

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r app/requirements.txt
python app/ingest.py
```

Dans ce cas, utilisez `QDRANT_URL=http://localhost:6333` si Qdrant est expose localement.
