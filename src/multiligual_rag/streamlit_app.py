"""Streamlit client for the IndicRAG-QA API."""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="IndicRAG-QA", page_icon="📚", layout="wide")
st.title("📚 IndicRAG-QA")
st.caption("Evidence-grounded question answering for English, Hindi, and Hinglish")

with st.sidebar:
    st.subheader("Knowledge base")
    st.caption(f"API: {API_URL}")
    uploads = st.file_uploader("Add PDF, TXT, or Markdown documents", type=["pdf", "txt", "md"], accept_multiple_files=True)
    if st.button("Index uploaded files", disabled=not uploads):
        progress = st.empty()
        for uploaded in uploads or []:
            try:
                response = requests.post(
                    f"{API_URL}/documents",
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")},
                    timeout=90,
                )
                response.raise_for_status()
                item = response.json()
                progress.success(f"Indexed {item['filename']} ({item['passage_count']} passages)")
            except requests.RequestException as exc:
                progress.error(f"Could not index {uploaded.name}: {exc}")
    try:
        docs = requests.get(f"{API_URL}/documents", timeout=5).json().get("documents", [])
        if docs:
            st.markdown("**Indexed documents**")
            for doc in docs:
                st.write(f"• {doc['filename']} — {doc['passage_count']} passages")
        else:
            st.info("Upload documents to get started.")
    except requests.RequestException:
        st.error("Backend is unavailable. Start the FastAPI server first.")

with st.form("question_form"):
    question = st.text_area("Ask in English, Hindi, or Hinglish", placeholder="Scholarship ke liye minimum eligibility kya hai?")
    left, middle, right = st.columns([2, 1, 1])
    method = left.selectbox("Retrieval strategy", ["hybrid", "lexical", "dense"], help="Compare character n-gram TF-IDF, English/Hindi multilingual embeddings, and rank fusion.")
    top_k = middle.slider("Passages", 1, 10, 5)
    submitted = right.form_submit_button("Ask", type="primary")

if submitted:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Searching documents and checking evidence…"):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question, "retrieval_method": method, "top_k": top_k},
                    timeout=180,
                )
                response.raise_for_status()
                result = response.json()
                if result["answerability"] == "ANSWERABLE":
                    st.success("ANSWERABLE")
                else:
                    st.warning("UNANSWERABLE — evidence was below the configured threshold")
                st.caption(f"Query type estimate: {result['query_type']}")
                st.markdown(result["answer"])
                st.caption(f"Strategy: {result['retrieval_method']} · Top evidence score: {result['evidence_score']} · {result['score_note']}")
                with st.expander("Retrieved evidence", expanded=True):
                    for source in result["sources"]:
                        page = f" · page {source['page']}" if source["page"] else ""
                        st.markdown(f"**[{source['passage_id']}] {source['document_name']}{page}** · score {source['score']}")
                        st.write(source["text"])
            except requests.RequestException as exc:
                detail = ""
                if getattr(exc, "response", None) is not None:
                    try:
                        detail = exc.response.json().get("detail", "")
                    except ValueError:
                        pass
                st.error(detail or f"Request failed: {exc}")

