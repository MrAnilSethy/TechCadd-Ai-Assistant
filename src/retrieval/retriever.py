from src.config import RETRIEVER_TOP_K
from src.retrieval.vectorstore import get_vectorstore

_retriever = None


def _get_cached_retriever():
    global _retriever
    if _retriever is None:
        _retriever = get_vectorstore().as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})
    return _retriever


def clear_retriever_cache() -> None:
    global _retriever
    _retriever = None


def retrieve(query: str):
    return _get_cached_retriever().invoke(query)
