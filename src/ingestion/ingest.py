import sys
from src.config import AUTO_SCRAPE_ON_INGEST
from src.ingestion.loader import load_documents
from src.ingestion.splitter import split_documents
from src.ingestion.web_scraper import scrape_website
from src.retrieval.retriever import clear_retriever_cache
from src.retrieval.vectorstore import rebuild_vectorstore


def run_ingestion(scrape: bool | None = None) -> tuple[int, int]:
    scrape = AUTO_SCRAPE_ON_INGEST if scrape is None else scrape
    if scrape:
        try:
            scrape_website()
        except Exception as exc:  # fall back to hand-written docs
            print(f"[ingest] scraping failed, using local documents only: {exc}")

    docs = load_documents()
    chunks = split_documents(docs)
    if not chunks:
        raise RuntimeError("No documents found in data/. Add .txt/.pdf files or enable scraping.")

    rebuild_vectorstore(chunks)
    clear_retriever_cache()
    return len(docs), len(chunks)


if __name__ == "__main__":
    n_docs, n_chunks = run_ingestion(scrape=None if len(sys.argv) < 2 else sys.argv[1] == "scrape")
    print(f"Done: {n_docs} documents, {n_chunks} chunks.")
