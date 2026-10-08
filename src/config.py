"""Central configuration. Values come from .env locally or from
Streamlit Cloud secrets (exposed as environment variables)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "techcadd_kb"

APP_NAME = "TechCADD AI Assistant"
ORG_NAME = "TechCADD Computer Education"
WEBSITE_URL = os.getenv("TECHCADD_WEBSITE_URL", "https://techcadd.com/")
CONTACT_PHONE = "+91 9888122255"

CATEGORIES = ["company", "courses", "admission", "career", "announcements"]

AUTO_SCRAPE_ON_INGEST = os.getenv("AUTO_SCRAPE_ON_INGEST", "true").lower() == "true"
MAX_SCRAPE_PAGES = int(os.getenv("MAX_SCRAPE_PAGES", "60"))
RETRIEVER_TOP_K = int(os.getenv("RETRIEVER_TOP_K", "5"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mistral-embed")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))


def missing_keys() -> list[str]:
    return [k for k in ("MISTRAL_API_KEY", "GROQ_API_KEY") if not os.getenv(k)]
