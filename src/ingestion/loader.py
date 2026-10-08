from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.config import CATEGORIES, DATA_DIR


def _load_txt(path: Path) -> list[Document]:
    """Scraped files start with 'Title:' / 'Source:' header lines; use them as metadata."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    meta = {"source": path.name, "title": ""}
    i = 0
    while i < len(lines) and (lines[i].startswith(("Title:", "Source:")) or not lines[i].strip()):
        if lines[i].startswith("Title:"):
            meta["title"] = lines[i].split(":", 1)[1].strip()
        elif lines[i].startswith("Source:"):
            meta["source"] = lines[i].split(":", 1)[1].strip()
        i += 1
    text = "\n".join(lines[i:]).strip()
    return [Document(page_content=text, metadata=meta)] if text else []


def load_documents() -> list[Document]:
    docs: list[Document] = []
    for category in CATEGORIES:
        folder = DATA_DIR / category
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            try:
                if path.suffix.lower() == ".txt":
                    loaded = _load_txt(path)
                elif path.suffix.lower() == ".pdf":
                    loaded = PyPDFLoader(str(path)).load()
                else:
                    continue
            except Exception as exc:  # one bad file should not stop ingestion
                print(f"[loader] skipped {path.name}: {exc}")
                continue
            for d in loaded:
                d.metadata["category"] = category
                d.metadata.setdefault("source", path.name)
                d.metadata["file"] = path.name
                d.metadata = {
                    k: v for k, v in d.metadata.items() if isinstance(v, (str, int, float, bool))
                }
            docs.extend(loaded)
    print(f"[loader] loaded {len(docs)} documents")
    return docs
