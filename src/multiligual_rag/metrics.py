"""Small dependency-light metrics for the project's retrieval and abstention experiments."""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def retrieval_metrics(ranked_passage_ids: Sequence[Sequence[str]], gold_passage_ids: Sequence[Iterable[str]], k: int = 5) -> dict[str, float]:
    """Compute macro Recall@K, Precision@K, Hit Rate@K, and MRR.

    Unanswerable examples should use an empty gold passage set and are excluded from
    retrieval metrics; evaluate those with answerability_metrics instead.
    """
    if len(ranked_passage_ids) != len(gold_passage_ids):
        raise ValueError("Ranked results and gold passage lists must have equal length.")
    recalls: list[float] = []
    precisions: list[float] = []
    hits: list[float] = []
    reciprocal_ranks: list[float] = []
    for ranked, gold_iter in zip(ranked_passage_ids, gold_passage_ids):
        gold = set(gold_iter)
        if not gold:
            continue
        top = list(ranked[:k])
        relevant = sum(pid in gold for pid in top)
        recalls.append(relevant / len(gold))
        precisions.append(relevant / k)
        hits.append(float(relevant > 0))
        reciprocal_ranks.append(next((1.0 / rank for rank, pid in enumerate(ranked, 1) if pid in gold), 0.0))
    if not recalls:
        return {"recall@k": 0.0, "precision@k": 0.0, "hit_rate@k": 0.0, "mrr": 0.0, "answerable_count": 0.0}
    return {
        "recall@k": sum(recalls) / len(recalls),
        "precision@k": sum(precisions) / len(precisions),
        "hit_rate@k": sum(hits) / len(hits),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "answerable_count": float(len(recalls)),
    }


def answerability_metrics(predicted: Sequence[bool], gold: Sequence[bool]) -> dict[str, float | int]:
    """Compute binary answerability accuracy, precision, recall, F1, and confusion counts."""
    if len(predicted) != len(gold):
        raise ValueError("Predictions and labels must have equal length.")
    tp = sum(p and g for p, g in zip(predicted, gold))
    tn = sum(not p and not g for p, g in zip(predicted, gold))
    fp = sum(p and not g for p, g in zip(predicted, gold))
    fn = sum(not p and g for p, g in zip(predicted, gold))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": (tp + tn) / len(gold) if gold else 0.0,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
    }
