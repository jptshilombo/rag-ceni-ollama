from app.rag_service import reindex_documents


def ingest_documents() -> dict[str, int | str]:
    def print_progress(step: str, current: int, total: int, message: str) -> None:
        if total > 1:
            percent = int((current / total) * 100)
            print(f"[{step}] {percent}% - {message}", flush=True)
        else:
            print(f"[{step}] {message}", flush=True)

    return reindex_documents(progress_callback=print_progress)


if __name__ == "__main__":
    result = ingest_documents()
    print(result)
