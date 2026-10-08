from langchain_core.tools import tool

from src.retrieval.retriever import retrieve


@tool
def retrieve_tool(query: str) -> str:
    """Search the TechCADD knowledge base (company, courses, admission, career,
    announcements). Use this for ANY question about TechCADD."""
    docs = retrieve(query)
    if not docs:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(
        f"[Chunk {i} | category: {d.metadata.get('category')} | source: {d.metadata.get('source')}]\n{d.page_content}"
        for i, d in enumerate(docs, 1)
    )
