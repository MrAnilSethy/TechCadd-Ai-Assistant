import uuid

import streamlit as st
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from src.agents.tools import retrieve_tool
from src.config import APP_NAME, CONTACT_PHONE, ORG_NAME, WEBSITE_URL, missing_keys
from src.ingestion.ingest import run_ingestion
from src.llm.model import get_llm
from src.prompts.prompts import SYSTEM_PROMPT
from src.retrieval.retriever import clear_retriever_cache
from src.retrieval.vectorstore import vectorstore_exists

st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="centered")

SAMPLE_QUESTIONS = [
    "Which AI and Data Science courses do you offer?",
    "Do you provide 6 months industrial training?",
    "How can I book a free demo class?",
    "Tell me about placement support.",
]


@st.cache_resource(show_spinner="Preparing the TechCADD knowledge base (first run only)...")
def init_knowledge_base() -> bool:
    if not vectorstore_exists():
        run_ingestion()
    return True


@st.cache_resource(show_spinner=False)
def get_agent():
    return create_agent(
        model=get_llm(),
        tools=[retrieve_tool],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),  # kept alive by cache_resource
    )


def _to_text(content) -> str:
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content)


def new_chat() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []


# ---------- guard: API keys ----------
if missing_keys():
    st.error(f"Missing environment variables: {', '.join(missing_keys())}")
    st.stop()

if "thread_id" not in st.session_state:
    new_chat()

init_knowledge_base()
agent = get_agent()

with st.sidebar:
    st.header(f"🎓 {ORG_NAME}")
    st.caption(f"Website: {WEBSITE_URL}")
    st.caption(f"Phone / WhatsApp: {CONTACT_PHONE}")
    if st.button("➕ New conversation", use_container_width=True):
        new_chat()
        st.rerun()
    if st.button("🔄 Refresh from website", use_container_width=True):
        with st.spinner("Scraping website and rebuilding knowledge base..."):
            try:
                n_docs, n_chunks = run_ingestion(scrape=True)
                clear_retriever_cache()
                st.success(f"Updated: {n_docs} documents, {n_chunks} chunks")
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")

st.title(APP_NAME)
st.caption("Ask about courses, industrial training, admissions, placements and events at TechCADD Jalandhar.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if not st.session_state.messages:
    cols = st.columns(2)
    for i, q in enumerate(SAMPLE_QUESTIONS):
        if cols[i % 2].button(q, use_container_width=True):
            st.session_state.pending = q
            st.rerun()

question = st.chat_input("Ask a question about TechCADD...") or st.session_state.pop("pending", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the knowledge base..."):
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    config={"configurable": {"thread_id": st.session_state.thread_id}},
                )
                answer = _to_text(result["messages"][-1].content)
            except Exception as exc:
                answer = f"Sorry, something went wrong while answering: `{exc}`"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
