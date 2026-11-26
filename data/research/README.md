# Research corpus snapshot and annotation status

**Snapshot date:** 2026-11-26
**Collection page supplied by the project owner:** <https://www.dohe-education.gov.in/department/our-bureaus/details/scholarships-education-loan-MDO2AjMtQWa>

The collection page returned HTTP 403 when checked on the snapshot date. The PDFs' internal titles, issuers, versions, page counts, extraction status, and SHA-256 hashes are recorded in [source_inventory.csv](source_inventory.csv). The issuer printed in a PDF is evidence of its stated provenance, not independent verification that this exact file was downloaded from the supplied page. No direct per-file download URLs were available for verification.

## Inventory findings

- Six English-language PDFs print a government or AICTE issuer. The EdCIL scholarship form is a seventh potential source, but its issuing host is not verified; the CSSS guidelines PDF is only four pages and needs a completeness check. Treat this as a frozen local snapshot, not as confirmation that a scheme is current.
- The eighth PDF, `ef7bc9fbc9e2ecd88358272a9a3d95c3.pdf`, is an image-only Bharti Airtel Foundation scholarship letter/annexure dated 2024-08-05. It is a real private-foundation document, not a fictional government policy; it is excluded from the government research corpus. `pdftotext` extracts no text from its eight pages, and OCR is not installed.
- Text extraction with Poppler `pdftotext -layout` returned text on all pages of the seven text-bearing files. The later exploratory evaluation also ran the project's Python extraction pipeline with `pypdf` 7.1.1 over the six government/AICTE-attributed candidate PDFs used for that run; the image-only private letter and pending-source EdCIL form were excluded.
- The government/AICTE-attributed source documents are English. There is no Hindi-source material in this snapshot. Hindi and Hinglish questions may be cross-lingual queries against English passages, but their translations, answerability, and reference answers need human review.
- There is no verified fictional PDF among the eight files currently in `sample_data/`. The former 15-row fictional demo seed has been removed; its referenced PDF is absent. Do not add fictional demo material to this corpus or research results.

## QA dataset status

[`qa_dataset_draft.jsonl`](qa_dataset_draft.jsonl) contains 378 machine-drafted examples, not a reviewed benchmark:

- 318 answerable examples are three language variants for each of the 106 entries in `csis-eligible-courses`. Their gold passage IDs were generated with the project chunking logic (900 characters, 120-character overlap) and checked to contain the course entry and its `Yes` marker.
- 60 deliberately unanswerable candidates are 20 out-of-domain questions in English, Hindi, and Hinglish. They are easy negatives; corpus-wide absence and all translations still need human review.
- The 126 fact clusters are split together: train 264 rows / 88 clusters, validation 57 / 19, and test 57 / 19. Each split has equal language-slice counts. No paraphrase or language variant crosses a split.
- Every row is marked `draft_unreviewed`. Hindi/Hinglish translations and generated reference answers are not reviewed; the candidate source's provenance is not independently verified. All answerable examples come from a single English course-list PDF, so this is a narrow annotation draft rather than a representative scholarship QA benchmark.

The [annotation_queue.csv](annotation_queue.csv) remains deliberately empty as a workflow/template, not a dataset or evaluation input. Review the draft row-by-row, correct/remove inaccurate questions and answers, verify all absence labels against the frozen corpus, and record reviewer and notes before moving accepted examples into a reviewed dataset. Follow [annotation_guide.md](annotation_guide.md); do not report draft metrics as research results.

An exploratory test-split run exists, but its labels and answers are unreviewed. See the [run report and metrics](../../research-results/draft-unreviewed-20261126T1940-k1/README.md); they are not validated research findings.
