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
- Run a local experiment comparing retrieval methods, RAG QA, and direct LLM QA, with threshold tuning on validation data and separate language-slice metrics.

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
- Poppler `pdftotext` is optional; it is used as an extraction fallback for PDFs whose embedded font maps produce corrupted text through `pypdf`.

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

### Current sample-document snapshot

The eight local PDFs were inventoried on 2026-11-26 in [data/research/source_inventory.csv](data/research/source_inventory.csv). Six English PDFs print government/AICTE issuers, one EdCIL form is pending issuer verification, and one image-only private-foundation scholarship letter is excluded from the government research corpus. The supplied collection page returned HTTP 403 during the provenance check. These files are local sample inputs, not a reviewed research benchmark. The legacy fictional demo seed has been removed; its referenced PDF is not present in `sample_data/`.

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

## Reproducible evaluation

Use a reviewed JSONL dataset with question, language slice, answerability, reference answer, and gold passage IDs. The schema and current annotation status are in [data/README.md](data/README.md) and [data/research/annotation_guide.md](data/research/annotation_guide.md). The former fictional demo seed has been removed and must not be used as research evidence.

The runner tunes retrieval evidence thresholds on validation examples, then writes `metrics.json` and `predictions.jsonl` for the chosen split. It compares lexical, dense, and hybrid retrieval with Recall@K, Precision@K, Hit Rate@K, and MRR; reports answerability metrics; and compares RAG with a direct Groq QA baseline. An exploratory top-k=1 run on the unreviewed draft is available in [research-results/](research-results/); it is not a validated benchmark. Token F1 is a coarse automatic metric for Hindi and Hinglish and does not certify correctness or faithfulness.

An unreviewed 378-row draft is available at [data/research/qa_dataset_draft.jsonl](data/research/qa_dataset_draft.jsonl); it is built from 106 course-list entries plus 20 easy out-of-domain candidates, with language variants grouped by fact. An exploratory run on its test split is saved under [research-results/](research-results/), but neither the dataset nor its metrics are validated research results. The [research corpus inventory](data/research/README.md) records the source snapshot; the annotation guide defines the review workflow. The official collection page returned HTTP 403 on 2026-11-26, and issuer/URL verification and some document-completeness checks remain outstanding. The former fictional demo seed has been removed; do not present draft-run or fictional demo outputs as validated research evidence.

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

Keep source inventory, provenance, gold passage IDs, answerability labels, and train/validation/test assignments. The draft dataset has 378 rows but remains unreviewed and narrowly sourced; the reviewed benchmark and 15-case analysis still need to be completed. The current [annotation queue](data/research/annotation_queue.csv) is empty. The former fictional demo seed has been removed.

`multiligual_rag.metrics` provides reusable retrieval, answerability, exact-match, and token-F1 metric functions. The experiment runner uses them and separates retrieval errors from answer-generation results.

## Limitations and next steps

- Index and uploaded files live only in process memory and are not shared across multiple workers.
- PDF extraction quality varies; verify extracted passages, especially tables and scanned PDFs. OCR is not included.
- The legacy fictional demo PDF is absent from the current `sample_data/`; the small fictional seed does not match the current corpus and is not research data.
- The current source snapshot is English-only and has unresolved source provenance/completeness questions. Hindi/Hinglish questions exist only in the unreviewed draft; there are no reviewed QA annotations or manual held-out analysis. The only run is exploratory and uses unreviewed labels. See [data/research/README.md](data/research/README.md) and [research-results/README.md](research-results/README.md).
- The English, Hindi, and Hinglish language/model combination has only been explored on the unreviewed draft, not benchmarked on reviewed data. Hinglish transliteration, rare terms, numbers, and names can fail.
- Retrieval-score thresholds are placeholders and can produce false answers or false abstentions.
- Citation IDs identify supplied excerpts; the system does not independently verify that each generated claim is entailed by its cited excerpt.
- Add a domain-specific labeled evaluation set, threshold calibration, answer/citation evaluation, language-slice metrics, and failure analysis before drawing research conclusions.

## Project layout

```text
src/multiligual_rag/
  api.py             FastAPI routes, upload extraction, and passage chunking
  graph.py           LangGraph answerability and grounded generation workflow
  retrieval.py       Lexical, multilingual dense, and hybrid retrievers
  metrics.py         Retrieval, answerability, and QA metrics
  evaluate.py        Direct-LLM/RAG comparison and report generation
  corpus.py          Shared document extraction and passage IDs
  streamlit_app.py   Streamlit frontend
```

