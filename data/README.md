# Dataset and experiment data

## What is in this directory

- The former 15-row fictional demo seed has been removed. Its referenced fictional PDF was not present in `sample_data/`; do not recreate or report its content as research evidence. The demo app and other assets are retained.
- `sources.json` is an earlier source note. The dated inventory of all eight current sample PDFs is [research/source_inventory.csv](research/source_inventory.csv).
- [research/](research/) contains the 2026-11-26 corpus snapshot, a 378-row **unreviewed draft** in `research/qa_dataset_draft.jsonl`, and an empty annotation queue. The draft is not a validated benchmark; the queue is a separate workflow template.

## Current research readiness

The current inventory identifies six English-language PDFs with government/AICTE issuers printed in the documents, one EdCIL form pending issuer verification, and one excluded image-only private-foundation scholarship letter. The supplied collection page returned HTTP 403 during the snapshot check; see the inventory for issuer evidence, version/date notes, page counts, extraction status, and hashes. The sources contain no Hindi-language material. The draft uses one English course-list PDF: its passage IDs were checked against the project's chunk format, but its questions, Hindi/Hinglish translations, reference answers, and out-of-domain absence labels have not been human-reviewed.

Do not claim a 300–500-example benchmark until the provenance and completeness checks in [research/annotation_guide.md](research/annotation_guide.md) are complete and human reviewers have annotated and reviewed the examples. Keep all paraphrases/translations of the same fact cluster within one split.

## Evaluation

The evaluation runner requires a reviewed dataset, project dependencies, a multilingual embedding model, and `GROQ_API_KEY` for QA generation. Dependencies were installed and an exploratory run on the unreviewed test split was completed; its [metrics and predictions](../research-results/draft-unreviewed-20261126T1940-k1/README.md) are not validated research results. Review the dataset before making performance claims, and keep research outputs separate from demo outputs.

## Future annotation fields

Use the header in `research/annotation_queue.csv`: question ID, fact-cluster ID, split, question, English/Hindi/Hinglish slice, answerability, evidence-grounded reference answer, actual gold passage IDs, unanswerable reason, difficulty tags, annotation status, reviewer, and review notes. See the annotation guide for the review gate and leakage-prevention procedure.
