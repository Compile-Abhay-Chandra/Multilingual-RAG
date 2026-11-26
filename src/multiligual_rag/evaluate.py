"""Run retrieval, answerability, RAG QA, and direct-LLM baseline experiments."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from multiligual_rag.corpus import extract_document
from multiligual_rag.graph import build_graph
from multiligual_rag.metrics import answerability_metrics, qa_metrics, retrieval_metrics
from multiligual_rag.retrieval import PassageIndex


METHODS = ("lexical", "dense", "hybrid")
THRESHOLDS = {"lexical": 0.10, "dense": 0.34, "hybrid": 0.34}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip() and not line.lstrip().startswith("#")]


def resolve_gold_passages(rows: list[dict], passages: list) -> None:
    normalized = [(passage, " ".join(passage.text.split())) for passage in passages]
    for item in rows:
        if item.get("gold_passage_ids") or not item.get("gold_passage_contains"):
            continue
        ids = []
        for phrase in item["gold_passage_contains"]:
            needle = " ".join(phrase.split())
            matches = [passage.id for passage, text in normalized if needle in text]
            if not matches:
                raise ValueError(f"Could not locate gold evidence text for example {item.get('id')}: {phrase}")
            ids.extend(matches)
        item["gold_passage_ids"] = sorted(set(ids))


def direct_answer(llm: ChatGroq, question: str) -> str:
    response = llm.invoke(
        "Answer concisely from general knowledge and use the same language as the question. If you do not know, say so. "
        "Do not claim to have consulted project documents.\n\nQuestion: " + question
    )
    return str(response.content)


def grouped_metrics(rows: list[dict], label_key: str) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(label_key, "unspecified"))].append(row)
    result = {}
    for label, items in sorted(groups.items()):
        answerable = [item for item in items if item["answerable"]]
        result[label] = {
            "count": len(items),
            "answerability": answerability_metrics(
                [item["predicted_answerable"] for item in items],
                [item["answerable"] for item in items],
            ),
            "retrieval": retrieval_metrics(
                [item["ranked_passage_ids"] for item in items],
                [item.get("gold_passage_ids", []) for item in items],
                k=max((len(item["ranked_passage_ids"]) for item in items), default=1),
            ),
            "rag_qa": qa_metrics([item["rag_answer"] for item in answerable], [item["reference_answer"] for item in answerable]),
            "direct_llm_qa": qa_metrics([item["direct_llm_answer"] for item in answerable], [item["reference_answer"] for item in answerable]),
        }
    return result


def calibrate_thresholds(index: PassageIndex, validation_rows: list[dict]) -> dict[str, float]:
    """Choose per-retriever evidence thresholds by answerability F1 on validation only."""
    calibrated: dict[str, float] = {}
    for method in METHODS:
        values = []
        labels = []
        for item in validation_rows:
            hits = index.search(item["question"], method=method, top_k=1)
            values.append(hits[0].evidence_score if hits else 0.0)
            labels.append(bool(item["answerable"]))
        candidates = sorted({0.0, 1.0, *values})
        best = (0.0, -1.0)
        selected = THRESHOLDS[method]
        for threshold in candidates:
            metrics = answerability_metrics([value >= threshold for value in values], labels)
            key = (float(metrics["f1"]), float(metrics["precision"]))
            if key > best:
                best, selected = key, threshold
        calibrated[method] = float(selected)
    return calibrated


def run(corpus_dir: Path, dataset_path: Path, output_dir: Path, split: str, top_k: int, calibration_path: Path | None = None) -> dict:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY must be set to run the QA and direct-LLM comparison.")
    docs = sorted(p for p in corpus_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md"})
    if not docs:
        raise ValueError(f"No PDF, TXT, or Markdown corpus files found under {corpus_dir}")
    passages = [passage for path in docs for passage in extract_document(path)]
    if not passages:
        raise ValueError("No extractable passages found in corpus documents.")
    all_rows = load_jsonl(dataset_path)
    resolve_gold_passages(all_rows, passages)
    rows = [item for item in all_rows if item.get("split", "test") == split]
    if not rows:
        raise ValueError(f"No examples for split '{split}' in {dataset_path}")
    known_passage_ids = {passage.id for passage in passages}
    for item in rows:
        missing = set(item.get("gold_passage_ids", [])) - known_passage_ids
        if missing:
            raise ValueError(f"Example {item.get('id')} refers to unknown passage IDs: {sorted(missing)}")

    index = PassageIndex()
    index.add(passages)
    validation_rows = load_jsonl(calibration_path) if calibration_path else [item for item in all_rows if item.get("split") == "validation"]
    resolve_gold_passages(validation_rows, passages)
    thresholds = calibrate_thresholds(index, validation_rows) if validation_rows else THRESHOLDS.copy()
    graph = build_graph(index, thresholds=thresholds)
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatGroq(model=model, temperature=0, api_key=api_key)
    predictions: list[dict] = []
    direct_cache: dict[str, str] = {}
    for item in rows:
        direct_cache[str(item.get("id", item["question"]))] = direct_answer(llm, item["question"])
    summaries: dict[str, dict] = {}

    for method in METHODS:
        method_rows: list[dict] = []
        ranked: list[list[str]] = []
        gold: list[list[str]] = []
        for item in rows:
            question = item["question"]
            hits = index.search(question, method=method, top_k=top_k)
            is_answerable = bool(hits and hits[0].evidence_score >= thresholds[method])
            graph_result = graph.invoke({"question": question, "method": method, "top_k": top_k})
            baseline = direct_cache[str(item.get("id", question))]
            result = {
                "id": item.get("id"),
                "question": question,
                "language_slice": item.get("language_slice", "unspecified"),
                "answerable": bool(item["answerable"]),
                "gold_passage_ids": item.get("gold_passage_ids", []),
                "reference_answer": item.get("reference_answer", ""),
                "retrieval_method": method,
                "ranked_passage_ids": [hit.passage.id for hit in hits],
                "retrieval_scores": [hit.score for hit in hits],
                "retrieved_passages": [
                    {"passage_id": hit.passage.id, "document_name": hit.passage.document_name, "page": hit.passage.page, "text": hit.passage.text}
                    for hit in hits
                ],
                "evidence_score": hits[0].evidence_score if hits else 0.0,
                "predicted_answerable": is_answerable,
                "rag_answer": graph_result.get("answer", ""),
                "direct_llm_answer": baseline,
            }
            predictions.append(result)
            method_rows.append(result)
            ranked.append(result["ranked_passage_ids"])
            gold.append(item.get("gold_passage_ids", []))

        answerable_rows = [item for item in method_rows if item["answerable"]]
        summaries[method] = {
            "retrieval": retrieval_metrics(ranked, gold, k=top_k),
            "answerability": answerability_metrics(
                [item["predicted_answerable"] for item in method_rows],
                [item["answerable"] for item in method_rows],
            ),
            "rag_qa": qa_metrics(
                [item["rag_answer"] for item in answerable_rows],
                [item["reference_answer"] for item in answerable_rows],
            ),
            "direct_llm_qa": qa_metrics(
                [item["direct_llm_answer"] for item in answerable_rows],
                [item["reference_answer"] for item in answerable_rows],
            ),
            "language_slices": grouped_metrics(method_rows, "language_slice"),
            "manual_unanswerable_review": [
                {
                    "id": item["id"],
                    "question": item["question"],
                    "rag_answer": item["rag_answer"],
                    "direct_llm_answer": item["direct_llm_answer"],
                    "retrieved_passages": item["retrieved_passages"],
                }
                for item in method_rows if not item["answerable"]
            ],
            "threshold_used": thresholds[method],
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps({"split": split, "count": len(rows), "thresholds_calibrated_on": "validation" if validation_rows else "uncalibrated_defaults", "thresholds": thresholds, "methods": summaries}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "predictions.jsonl").open("w", encoding="utf-8") as destination:
        for item in predictions:
            destination.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {"split": split, "count": len(rows), "methods": summaries}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True, help="Directory containing source PDF/TXT/Markdown files")
    parser.add_argument("--dataset", type=Path, required=True, help="Labeled JSONL dataset")
    parser.add_argument("--calibration-dataset", type=Path, help="Optional validation JSONL used only for threshold calibration")
    parser.add_argument("--output", type=Path, default=Path("results/run"))
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    summary = run(args.corpus, args.dataset, args.output, args.split, args.top_k, args.calibration_dataset)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
