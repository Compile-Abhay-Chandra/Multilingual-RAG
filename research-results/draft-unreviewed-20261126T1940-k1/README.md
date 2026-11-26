# Exploratory draft evaluation (not research results)

**Status:** completed pipeline run on the unreviewed draft dataset. These numbers are exploratory only; the labels, translations, and reference answers have not been human-reviewed.

## Run setup

- Dataset: `data/research/qa_dataset_draft.jsonl`, SHA-256 `3742c2ba6551e1ff735f2a4eeb0d0b4bfde24a69fad45bc31d86843337a24fdb`.
- Corpus: six government/AICTE-attributed candidate PDFs listed in `data/research/source_inventory.csv`. The unverified EdCIL form and private Bharti Airtel letter were excluded. The collection-page association remains unverified, and the four-page CSSS guideline's completeness is unresolved.
- Split: test, 57 rows (48 answerable and 9 unanswerable candidates); 19 rows per language slice.
- Retrieval: top-k = 1. Thresholds were calibrated on the draft validation split: lexical 0.1275708724, dense 0.5149211884, hybrid 0.4343812764.
- Runtime: Python 3.14.10; `pypdf` 7.1.1; scikit-learn 1.9.1; sentence-transformers 6.3.0; langchain-groq 1.2.1; langgraph 1.2.24; Groq model `openai/gpt-oss-120b`.
- The one-off invocation set the Groq client retry limit to 8 after the default retry setting hit a TPM limit. This retry override is not checked into the project runner. A prior top-k=5 attempt stopped on a rate-limit error and wrote no output.

## Exploratory matrices

| Method | Recall@1 / Hit Rate@1 | Answerability F1 | RAG token F1 | Direct-LLM token F1 | Exact match |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lexical | 0.5833 | 0.9895 | 0.4696 | 0.1505 | 0.0000 |
| Dense | 0.0000 | 0.9895 | 0.3053 | 0.1505 | 0.0000 |
| Hybrid | 0.2083 | 1.0000 | 0.3828 | 0.1505 | 0.0000 |

These are automatic scores on unreviewed, highly templated labels. The test set contains only three easy out-of-domain unanswerable clusters per language. Token F1 is especially coarse for Hindi and Hinglish; none of these numbers establish model quality or support a research conclusion.

## Files

- [`metrics.json`](metrics.json): complete metrics, validation-selected thresholds, language slices, and unanswerable review candidates.
- [`predictions.jsonl`](predictions.jsonl): 171 predictions (57 test questions × 3 retrieval methods).

No API key or other secret is stored in this directory.
