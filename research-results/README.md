# Research results status

**Snapshot date:** 2026-11-26
**Status:** an exploratory metrics run and predictions exist, but no validated research results are available.

The [`data/research/qa_dataset_draft.jsonl`](../data/research/qa_dataset_draft.jsonl) file contains 378 unreviewed draft examples; it is not a reviewed test split and must not be used to claim research performance. Dependencies were installed from `uv.lock` using Python 3.14.10, and the configured Groq key was used without displaying or saving its value. The source page returned HTTP 403 during provenance review; a configured API key cannot substitute for reviewed labels or verified source provenance.

The completed exploratory run is in [`draft-unreviewed-20261126T1940-k1/`](draft-unreviewed-20261126T1940-k1/). It covers all 57 draft test rows and all three retrieval methods at top-k 1; thresholds were calibrated on the unreviewed validation split. The run README records settings and headline metrics. The six-file candidate corpus excludes the pending-source EdCIL form and the private letter. All reported metrics remain draft-only because questions, translations, reference answers, and unanswerable labels have not been reviewed. The 15-case qualitative analysis is still pending human review.

Keep demo outputs separate and never present draft-run outputs as validated research results. The legacy fictional seed has been removed. No secrets or API keys belong in this directory.
