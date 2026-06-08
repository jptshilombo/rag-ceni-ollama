from app.rag_service import reindex_documents


def ingest_documents() -> dict[str, int | str]:
    return reindex_documents()


if __name__ == "__main__":
    result = ingest_documents()
    print(result)
