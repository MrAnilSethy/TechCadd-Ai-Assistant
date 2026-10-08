import time

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings

from src.config import CHROMA_DIR, COLLECTION_NAME, EMBED_BATCH_SIZE, EMBED_MODEL


def get_embeddings() -> MistralAIEmbeddings:
    return MistralAIEmbeddings(model=EMBED_MODEL)


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def vectorstore_exists() -> bool:
    if not CHROMA_DIR.exists():
        return False
    try:
        return get_vectorstore()._collection.count() > 0
    except Exception:
        return False


def rebuild_vectorstore(chunks: list[Document]) -> Chroma:
    """Drop the old collection and re-embed everything (batched to respect rate limits)."""
    try:
        get_vectorstore().delete_collection()
    except Exception:
        pass
    store = get_vectorstore()
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        store.add_documents(chunks[i : i + EMBED_BATCH_SIZE])
        time.sleep(0.5)
    print(f"[vectorstore] stored {len(chunks)} chunks")
    return store
