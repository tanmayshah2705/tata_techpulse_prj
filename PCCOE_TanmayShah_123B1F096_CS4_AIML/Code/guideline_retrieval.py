"""
guideline_retrieval.py
AutoCodeGuard — TF-IDF-based guideline retrieval from a local JSON knowledge base.

No external models or downloads are required.
"""

import json
import os
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

_KB_PATH = os.path.join(os.path.dirname(__file__), "guidelines_kb.json")


class GuidelineRetriever:
    """
    Loads the JSON knowledge base and indexes it with TF-IDF.
    Call retrieve(query, top_k) to get the most relevant guidelines.
    """

    def __init__(self, kb_path: str = _KB_PATH):
        with open(kb_path, "r", encoding="utf-8") as fh:
            self._guidelines: List[Dict] = json.load(fh)

        # Build corpus: combine title + description + tags for each guideline
        corpus = []
        for g in self._guidelines:
            tags_str = " ".join(g.get("tags", []))
            text = f"{g['title']} {g['description']} {tags_str}"
            corpus.append(text)

        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Return up to *top_k* guidelines most relevant to *query*.
        Each returned dict includes all KB fields plus a 'score' key.
        """
        if not query or not query.strip():
            return []

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.0:
                entry = dict(self._guidelines[idx])
                entry["score"] = float(scores[idx])
                results.append(entry)
        return results

    def retrieve_for_finding(self, finding: dict, top_k: int = 2) -> List[Dict]:
        """Convenience wrapper: build query from a finding dict."""
        query = " ".join(filter(None, [
            finding.get("title", ""),
            finding.get("explanation", ""),
            finding.get("evidence", ""),
        ]))
        return self.retrieve(query, top_k=top_k)

    @property
    def all_guidelines(self) -> List[Dict]:
        return list(self._guidelines)


# Module-level singleton (lazy)
_retriever: GuidelineRetriever | None = None


def get_retriever() -> GuidelineRetriever:
    global _retriever
    if _retriever is None:
        _retriever = GuidelineRetriever()
    return _retriever
