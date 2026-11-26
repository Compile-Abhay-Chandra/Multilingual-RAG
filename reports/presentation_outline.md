# IndicRAG-QA Presentation Outline

> **Research draft status (snapshot 2026-11-26):** a 378-row machine-drafted QA set and an exploratory test-split run exist, but none of the labels are human-reviewed. Do not present the metrics below as validated research findings.

1. **Problem** — English, Hindi, and Hinglish questions may need evidence from documents written in another language.
2. **Research questions** — lexical vs dense vs hybrid retrieval; direct QA vs RAG; answerability and abstention.
3. **Corpus snapshot (verified locally)** — six PDFs with government/AICTE issuers, one EdCIL form pending issuer verification, one excluded image-only private-foundation letter, extraction checks, and unresolved source-link/completeness checks. See `data/research/source_inventory.csv`.
4. **System architecture** — Streamlit → FastAPI → retrieval → LangGraph evidence check → Groq answer with cited passages.
5. **Exploratory retrieval matrix (draft only)** — test split n=57, top-k=1: lexical Recall@1/Hit@1 0.583, dense 0.000, hybrid 0.208. Labels are unreviewed and the set is narrowly sourced; do not infer comparative research performance.
6. **Exploratory QA and answerability (draft only)** — answerability F1: lexical 0.989, dense 0.989, hybrid 1.000; RAG token F1: 0.470, 0.305, 0.383 respectively; direct-LLM token F1 0.150; exact match 0.000 for all. Automatic scores and labels are unreviewed; no quality conclusion.
7. **Difficult cases (pending human review)** — select and manually analyze at least 15 difficult cases after the draft labels and test split are reviewed.
8. **Current limitations and next steps** — collection page returned HTTP 403; EdCIL origin and CSSS guideline completeness need review; the draft uses one English PDF and has unreviewed Hindi/Hinglish translations and easy out-of-domain negatives; empty review queue; manually review labels and 15 difficult cases before any research claims.
