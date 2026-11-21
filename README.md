# IndicRAG-QA

An evidence-grounded document question-answering starter for **English, Hindi, and Hinglish**. The application combines a **FastAPI** service, a **LangGraph** retrieve/assess/answer workflow, **Groq** for answer generation, and a **Streamlit** interface.

This is an implementation of the supplied project idea, not a claim that multilingual retrieval or abstention is novel. It provides an extensible demo and baseline experiments; evaluate it on a labeled domain dataset before making performance claims.

## What it does

- Upload PDF, TXT, or Markdown documents. PDFs are split by page and preserve page numbers in citations.
- Split extracted text into overlapping passages with stable passage IDs.
- Compare **lexical** character n-gram TF-IDF, **dense** multilingual sentence embeddings, and **hybrid** reciprocal-rank fusion.
- Use a LangGraph workflow to retrieve passages, apply a configurable starter evidence threshold, and either abstain or call Groq.
- Require the answer to use only retrieved excerpts and cite passage IDs. Return the retrieved excerpts and scores for inspection.
- Ask in English, Hindi (Devanagari), or Hinglish. Although the selected embedding model covers additional languages, this project's supported query languages are limited to these three; evaluate performance on your own dataset.

## Architecture

```text
Streamlit UI  ──HTTP──>  FastAPI
                            ├── document extraction and chunking
                            ├── lexical / dense / hybrid retrieval
                            └── LangGraph: retrieve → assess → answer or abstain
                                                   └── Groq Chat Completions
```

The starter stores documents and indexes in memory. Restarting the API clears uploaded documents. Use a persistent database/vector store before deploying or using a large collection.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A Groq API key for answer generation (get one in the [Groq Console](https://console.groq.com/))
- Internet access on the first dense retrieval request to download the multilingual embedding model

## Setup

```bash
uv sync
cp .env.example .env
```

Set `GROQ_API_KEY` in `.env`. Optionally change `GROQ_MODEL`; the default is `llama-3.3-70b-versatile`.

## Run

Start the API in one terminal:

```bash
uv run uvicorn multiligual_rag.api:app --app-dir src --reload --port 8000
```

Start the UI in a second terminal:

```bash
uv run streamlit run src/multiligual_rag/streamlit_app.py
```

Open the local URL printed by Streamlit. Add documents in the sidebar, choose a retrieval strategy, and ask a question. FastAPI's interactive API docs are at `http://localhost:8000/docs`; health is at `/health`.

### Try the sample PDF

Upload [`sample_data/demo_scholarship_policy.pdf`](sample_data/demo_scholarship_policy.pdf) in the sidebar. It is a six-page Hindi document with fictional scholarship details for testing and is not about a real scholarship. The editable Hindi source is [`sample_data/demo_scholarship_policy_hi.html`](sample_data/demo_scholarship_policy_hi.html). Try questions such as:

- English: “What is the minimum exam score?”
- Hindi: “छात्रवृत्ति के लिए न्यूनतम अंक कितने चाहिए?”
- Hinglish: “Scholarship ke liye minimum marks kitne chahiye?”
- Abstention: “विश्वविद्यालय के पुस्तकालय के खुलने का समय क्या है?” (the sample does not cover library hours)

To point Streamlit at a different API server, set `API_URL`, for example `API_URL=http://127.0.0.1:8000`.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service and index counts |
| `GET` | `/documents` | List indexed documents |
| `POST` | `/documents` | Upload one PDF, TXT, or Markdown file (`multipart/form-data`, field `file`) |
| `DELETE` | `/documents/{document_id}` | Remove a document and its passages |
| `POST` | `/ask` | Retrieve evidence and answer or abstain |

Example question request:

```json
{
  "question": "Scholarship ke liye minimum eligibility kya hai?",
  "retrieval_method": "hybrid",
  "top_k": 5
}
```

The response includes `ANSWERABLE`/`UNANSWERABLE`, a lightweight language estimate in `query_type` (`english-likely`, `hindi`, or `hinglish-likely`), an answer, an evidence score, the retrieval strategy, and source passages with document/page/passage identifiers. The language estimate is a simple heuristic, not a language-identification model. The scores and current abstention thresholds are **uncalibrated starter heuristics**. Tune them on a validation split and report held-out results. Do not treat the returned score as calibrated confidence.

## Retrieval and model notes

- **Lexical:** scikit-learn character n-gram TF-IDF helps with names, spelling variation, and some transliteration overlap.
- **Dense:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` embeds queries and passages into a shared multilingual space. Dense index creation is lazy; its first use downloads the model. The app's intended support is English, Hindi, and Hinglish, even though the encoder itself covers other languages.
- **Hybrid:** reciprocal-rank fusion combines rankings without assuming that TF-IDF and cosine values share a score scale.
- **Generation:** only runs when the best retrieval result clears a starter threshold. Groq answers from the retrieved context and is instructed to cite passage IDs.

For a fair experiment, fix the corpus, chunking, top-k, embedding model, model/prompt, and data split. Use a validation set to choose thresholds/settings; report metrics on a held-out test set. Include enough answerable and deliberately unanswerable examples and report results separately for English, Hindi, and Hinglish queries.

## Suggested evaluation dataset

Create a JSONL file with one object per question. For example:

```json
{"question":"What is the application deadline?","relevant_passage_ids":["a1b2-p2-c1"],"answerable":true,"language_slice":"english"}
{"question":"Scholarship ke liye travel allowance milta hai?","relevant_passage_ids":[],"answerable":false,"language_slice":"hinglish"}
```

Keep source inventory, provenance, gold passage IDs, answerability labels, and train/development/test assignments. The project proposal suggests roughly 300–500 examples and at least 15 analyzed difficult cases. The current repository provides the serving and retrieval baseline; answer correctness, citation support, and answerability still need human or task-specific evaluation.

`multiligual_rag.metrics` includes reusable `retrieval_metrics(...)` (Recall@K, Precision@K, Hit Rate@K, MRR on answerable questions) and `answerability_metrics(...)` (accuracy, precision, recall, F1, and confusion counts). Call these from an experiment script with ranked passage IDs and gold labels for each retrieval method, then report language slices separately.

## Limitations and next steps

- Index and uploaded files live only in process memory and are not shared across multiple workers.
- PDF extraction quality varies; verify extracted passages, especially tables and scanned PDFs. OCR is not included.
- The English, Hindi, and Hinglish language/model combination has not been benchmarked here. Hinglish transliteration, rare terms, numbers, and names can fail.
- Retrieval-score thresholds are placeholders and can produce false answers or false abstentions.
- Citation IDs identify supplied excerpts; the system does not independently verify that each generated claim is entailed by its cited excerpt.
- Add a domain-specific labeled evaluation set, threshold calibration, answer/citation evaluation, language-slice metrics, and failure analysis before drawing research conclusions.

## Project layout

```text
src/multiligual_rag/
  api.py             FastAPI routes, upload extraction, and passage chunking
  graph.py           LangGraph answerability and grounded generation workflow
  retrieval.py       Lexical, multilingual dense, and hybrid retrievers
  metrics.py         Retrieval and answerability evaluation metrics
  streamlit_app.py   Streamlit frontend
```

