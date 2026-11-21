"""In-memory lexical, multilingual dense, and rank-fusion retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RetrievalMethod = Literal["lexical", "dense", "hybrid"]


@dataclass
class Passage:
    id: str
    document_id: str
    document_name: str
    text: str
    page: int | None = None


@dataclass
class Hit:
    passage: Passage
    score: float
    evidence_score: float


class PassageIndex:
    """Small project/demo index. It can be replaced by a persistent vector store later."""

    def __init__(self) -> None:
        self.passages: list[Passage] = []
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=1, sublinear_tf=True)
        self.lexical_matrix = None
        self._dense_matrix: np.ndarray | None = None

    def add(self, passages: list[Passage]) -> None:
        known_ids = {p.id for p in self.passages}
        self.passages.extend(p for p in passages if p.id not in known_ids)
        self._rebuild()

    def remove_document(self, document_id: str) -> None:
        self.passages = [p for p in self.passages if p.document_id != document_id]
        self._rebuild()

    def _rebuild(self) -> None:
        self._dense_matrix = None
        if not self.passages:
            self.lexical_matrix = None
            return
        self.lexical_matrix = self.vectorizer.fit_transform([p.text for p in self.passages])

    @staticmethod
    @lru_cache(maxsize=1)
    def _encoder():
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    def _dense_search(self, query: str) -> np.ndarray:
        if self._dense_matrix is None:
            self._dense_matrix = self._encoder().encode(
                [p.text for p in self.passages], normalize_embeddings=True, show_progress_bar=False
            )
        query_vector = self._encoder().encode([query], normalize_embeddings=True, show_progress_bar=False)
        return cosine_similarity(query_vector, self._dense_matrix)[0]

    def search(self, query: str, method: RetrievalMethod = "hybrid", top_k: int = 5) -> list[Hit]:
        if not self.passages or not query.strip():
            return []
        lexical = cosine_similarity(self.vectorizer.transform([query]), self.lexical_matrix)[0]
        if method == "lexical":
            scores = lexical
            evidence_scores = lexical
        elif method == "dense":
            scores = self._dense_search(query)
            evidence_scores = scores
        else:
            # Reciprocal rank fusion avoids mixing uncalibrated lexical and cosine scales.
            dense = self._dense_search(query)
            lexical_order = np.argsort(-lexical)
            dense_order = np.argsort(-dense)
            fused = np.zeros(len(self.passages), dtype=float)
            for rank, idx in enumerate(lexical_order, start=1):
                fused[idx] += 1.0 / (60 + rank)
            for rank, idx in enumerate(dense_order, start=1):
                fused[idx] += 1.0 / (60 + rank)
            scores = fused
            # Use the stronger raw signal for the abstention heuristic. RRF ranks are
            # useful for ordering but their absolute values depend on corpus size.
            evidence_scores = np.maximum(lexical, dense)
        order = np.argsort(-scores)[: max(1, min(top_k, len(self.passages)))]
        return [Hit(self.passages[int(i)], float(scores[i]), float(evidence_scores[i])) for i in order]

