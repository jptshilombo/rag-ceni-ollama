import hashlib
import re
from pathlib import Path
from typing import Iterable

from docx import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from config import QDRANT_URL
from ocr_utils import extract_text_from_pdf
from ollama_client import embed


COLLECTION_NAME = "ceni_docs"
VECTOR_SIZE = 4096
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CHUNK_SIZE_CHARS = 1_800
CHUNK_OVERLAP_CHARS = 250


def ensure_collection(client: QdrantClient) -> None:
    existing = [collection.name for collection in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    document = Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(str(path))
    if suffix == ".txt":
        return read_txt(path)
    if suffix == ".docx":
        return read_docx(path)
    raise ValueError(f"Unsupported file type: {path}")


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE_CHARS, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - CHUNK_OVERLAP_CHARS)
    return chunks


def infer_type_document(filename: str) -> str:
    name = filename.lower()
    if any(token in name for token in ["pv", "proces-verbal", "proces_verbal", "proces verbal"]):
        return "pv"
    if any(token in name for token in ["loi", "legal", "constitution"]):
        return "loi"
    if any(token in name for token in ["rapport", "audit", "mission"]):
        return "rapport"
    return "autre"


def infer_cycle_electoral(filename: str) -> str | None:
    match = re.search(r"(19|20)\d{2}", filename)
    return match.group(0) if match else None


def iter_documents(data_dir: Path) -> Iterable[Path]:
    supported = {".pdf", ".txt", ".docx"}
    return (
        path
        for path in sorted(data_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in supported
    )


def make_point_id(filename: str, chunk_index: int) -> int:
    digest = hashlib.sha256(f"{filename}:{chunk_index}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def ingest_documents() -> None:
    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client)

    points: list[PointStruct] = []
    for path in iter_documents(DATA_DIR):
        text = read_document(path)
        chunks = chunk_text(text)
        type_document = infer_type_document(path.name)
        cycle_electoral = infer_cycle_electoral(path.name)

        for index, chunk in enumerate(chunks):
            payload = {
                "filename": path.name,
                "path": str(path.relative_to(DATA_DIR)),
                "type_document": type_document,
                "cycle_electoral": cycle_electoral,
                "chunk_index": index,
                "text": chunk,
            }
            points.append(
                PointStruct(
                    id=make_point_id(path.name, index),
                    vector=embed(chunk),
                    payload=payload,
                )
            )

            if len(points) >= 32:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                points.clear()

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)


if __name__ == "__main__":
    ingest_documents()
