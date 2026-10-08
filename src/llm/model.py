from langchain_groq import ChatGroq

from src.config import GROQ_MODEL


def get_llm() -> ChatGroq:
    return ChatGroq(model=GROQ_MODEL, temperature=0.2)
