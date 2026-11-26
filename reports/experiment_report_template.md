# IndicRAG-QA: Experimental Report (Draft)

> **Status: exploratory research draft, corpus snapshot 2026-11-26.** A 378-row dataset and test-split metrics exist, but no examples have been human-reviewed. The results below are exploratory automatic scores, not validated research findings. Never substitute demo-seed output for research results.

## Abstract

The project proposes evidence-grounded scholarship and education-loan question answering over public documents. Six local English-language PDFs print government/AICTE issuers, one EdCIL form has an unverified issuing host, and one image-only private-foundation letter is excluded. The collection page could not be independently accessed during provenance review (HTTP 403). An exploratory run was completed on an unreviewed held-out split; no validated benchmark or experimental conclusion is available.

## 1. Problem and research questions

- RQ1: Does multilingual dense retrieval outperform lexical retrieval for Hindi and Hinglish queries?
- RQ2: Does hybrid retrieval improve retrieval metrics?
- RQ3: How do English, Hindi, cross-lingual, and code-mixed slices compare?
- RQ4: Does RAG improve answer correctness and reduce unsupported answers compared with direct LLM QA?
- RQ5: What answerability threshold trades off false answers and false abstentions?

## 2. Corpus and dataset

The inventory and file hashes are in [source_inventory.csv](../data/research/source_inventory.csv). Snapshot date: 2026-11-26. Six government/AICTE-attributed PDFs and the EdCIL form yielded text from all pages with Poppler `pdftotext -layout`; the EdCIL issuer/host is unverified. The eighth PDF is an image-only Bharti Airtel Foundation document and is excluded as private/non-government. The collection page returned HTTP 403, so exact file-to-page provenance remains unverified. Completeness of the four-page CSSS guidelines also needs confirmation. PDF metadata timestamps are recorded separately and are not treated as publication dates.

The unreviewed [`qa_dataset_draft.jsonl`](../data/research/qa_dataset_draft.jsonl) contains 378 rows: 318 answerable course-list variants across 106 fact clusters, plus 60 easy out-of-domain unanswerable candidates across 20 clusters. It uses English, Hindi, and Hinglish question slices and keeps all variants of each fact in one split. The answerable set is derived from one English PDF; translations, reference answers, labels, and absence judgments still need human review. Passage IDs were generated using the project's 900-character/120-overlap chunking with `pypdf` 7.1.1. Annotation instructions and the still-empty review queue are in [annotation_guide.md](../data/research/annotation_guide.md) and [annotation_queue.csv](../data/research/annotation_queue.csv).

| Draft split (unreviewed) | Questions | Answerable | Unanswerable | English | Hindi | Hinglish |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 264 | 222 | 42 | 88 | 88 | 88 |
| Validation | 57 | 48 | 9 | 19 | 19 | 19 |
| Test | 57 | 48 | 9 | 19 | 19 | 19 |
| Total | 378 | 318 | 60 | 126 | 126 | 126 |

These are generated row counts, not reviewed-example counts; reviewed count is zero.

## 3. Methods

The checked-in evaluation implementation uses character n-gram TF-IDF, a multilingual sentence encoder, reciprocal-rank fusion, threshold calibration on validation data, RAG, and a direct Groq baseline. The exploratory run used the full 57-row draft test split, top-k 1, Python 3.14.10, and `openai/gpt-oss-120b`; thresholds were calibrated on the draft validation split. The run used a one-off client retry limit of 8 after a TPM limit; this override is not in the checked-in runner. See the run metadata in [research-results/draft-unreviewed-20261126T1940-k1/README.md](../research-results/draft-unreviewed-20261126T1940-k1/README.md). All labels remain unreviewed.

## 4. Results

### Retrieval

| Method | Recall@1 / Hit Rate@1 | Answerability F1 | RAG token F1 | Direct-LLM token F1 | Exact match |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lexical | 0.5833 | 0.9895 | 0.4696 | 0.1505 | 0.0000 |
| Dense | 0.0000 | 0.9895 | 0.3053 | 0.1505 | 0.0000 |
| Hybrid | 0.2083 | 1.0000 | 0.3828 | 0.1505 | 0.0000 |

The test split has 57 rows (48 answerable and 9 unanswerable candidates), with 19 rows per language slice. All 48 answerable labels and all 9 unanswerable labels are unreviewed; the negatives are easy out-of-domain examples. The metrics are therefore descriptive of this draft run only. Precision@1, Recall@1, Hit Rate@1, and MRR are equal here because only one passage is retrieved and each answerable item has one gold passage.

| Language slice | Lexical Hit@1 | Dense Hit@1 | Hybrid Hit@1 | Lexical RAG token F1 | Dense RAG token F1 | Hybrid RAG token F1 | Direct token F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| English (n=19) | 0.4375 | 0.0000 | 0.1875 | 0.5216 | 0.3839 | 0.4249 | 0.0426 |
| Hindi (n=19) | 0.8125 | 0.0000 | 0.3750 | 0.5233 | 0.2923 | 0.4703 | 0.1548 |
| Hinglish (n=19) | 0.5000 | 0.0000 | 0.0625 | 0.3639 | 0.2397 | 0.2532 | 0.2541 |

Exact match is 0 for all methods and slices. Token F1 is a coarse automatic metric, particularly for Hindi/Hinglish; no manual answer or citation review was performed. Full metrics and predictions are in [the draft run directory](../research-results/draft-unreviewed-20261126T1940-k1/).

### QA and answerability

The runner produced predictions, but no human review of answers, citations, or the unanswerable cases has been conducted. The 15-case analysis remains pending. Do not report these draft-dataset scores or demo-seed results as validated research results.

## 5. Error analysis

Analyze at least 15 held-out difficult cases: code-mixing, spelling/transliteration, named entities, numbers/dates, ambiguity, and semantically similar passages. For each, state whether gold evidence was retrieved, whether the answer was correct and supported, likely failure stage, and a specific fix. Include false answers and false abstentions.

| Case ID | Language/type | Difficulty | Gold evidence retrieved? | Answer supported? | Failure cause | Proposed fix |
| --- | --- | --- | --- | --- | --- | --- |
| Pending human review: no reviewed test set or prediction analysis | | | | | | |

## 6. Discussion and limitations

Interpret results without overclaiming. Discuss language coverage, source quality, annotation noise, dataset size, threshold calibration, model/prompt dependence, and citation-support review.

## 7. Conclusion

[Answer each research question using held-out results.]

## Reproducibility

The exploratory run's dataset hash, corpus scope, model, thresholds, and settings are recorded in [its README](../research-results/draft-unreviewed-20261126T1940-k1/README.md); metrics and predictions are in the same directory. The inventory hashes are in `data/research/source_inventory.csv`. No API secrets are included. Re-run only after human review and freeze the accepted dataset before making research claims.
