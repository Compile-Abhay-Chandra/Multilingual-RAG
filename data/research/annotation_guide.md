# QA annotation workflow (draft)

**Status:** annotation workflow for the unreviewed [`qa_dataset_draft.jsonl`](qa_dataset_draft.jsonl). It contains 378 machine-drafted rows; none have been human-reviewed. Do not report it as a validated benchmark.

## Before annotation

1. Verify the exact original URL and issuing authority for each candidate PDF in `source_inventory.csv`. Resolve the EdCIL issuer and check whether the four-page CSSS guideline is complete. Record any superseded material rather than silently mixing versions.
2. Freeze the accepted PDFs and this inventory. Keep the SHA-256 hashes. The current draft's passage IDs use `corpus.py` chunking (900 characters, 120-character overlap) with locked `pypdf` 7.1.1. Recompute and verify IDs if the corpus, extraction library, or chunking changes; do not hand-author passage IDs.
3. Keep the excluded private-foundation letter outside the government research corpus. If a separate private-scholarship study is desired, create a separately scoped corpus with its own provenance review.

## Fill `annotation_queue.csv`

- Add one independently answerable or deliberately unanswerable question per row. Create the question from a fact or a clearly absent fact in the frozen corpus; do not invent its answer.
- `fact_cluster_id` identifies the underlying fact or evidence unit. Put every paraphrase, spelling variation, translation, and code-mixed variant of the same fact in the **same split**. Assign splits by cluster, not by row, to prevent leakage.
- Use `language_slice` values `english`, `hindi`, or `hinglish`. Label the wording actually used, not the language of the source. Hindi/Hinglish translations require fluent human review.
- For answerable questions, fill the reference answer from the cited passage(s), cite actual frozen passage IDs in `gold_passage_ids`, and ensure the evidence entails the complete answer. Multiple evidence passages are allowed where genuinely needed.
- For unanswerable questions, use `answerable=false`, leave evidence IDs empty, and explain precisely what information the accepted corpus lacks. “Not found” does not mean the answer is false in the real world.
- Add difficulty tags such as `code-mixed`, `transliteration`, `named-entity`, `numeric`, `date`, `ambiguity`, `near-duplicate`, or `cross-lingual` only when applicable.
- Mark the row `reviewed` only after a human has checked language, answerability, reference wording, evidence passage(s), and split group. Record the reviewer. Do not describe machine-generated or self-authored labels as independently reviewed.
- The current draft's answerable examples all come from one English course-list PDF and use templated questions. Its unanswerable examples are easy out-of-domain candidates, not verified hard negatives. Add broader, independently reviewed facts and difficult cases before treating the set as representative.

## Suggested release gate

Target approximately 300–500 reviewed examples only if the verified corpus supports them. Include all three query slices and both answerability labels; report counts rather than claiming balance that is not present. Keep fact clusters disjoint across train, validation, and test. Use validation only for threshold/model selection. Freeze the test set before experiments and review at least 15 difficult held-out cases after running the pipeline.

## Required row fields

The empty [annotation_queue.csv](annotation_queue.csv) header is the CSV workflow schema: `id`, `fact_cluster_id`, `split`, `question`, `language_slice`, `answerable`, `reference_answer`, `gold_passage_ids`, `unanswerable_reason`, `difficulty_tags`, `annotation_status`, `reviewer`, and `review_notes`. The draft JSONL also records source document/page and draft method. Store list-valued fields as JSON arrays in CSV cells.
