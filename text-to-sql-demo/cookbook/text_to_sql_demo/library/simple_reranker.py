"""Lightweight semantic reranker used for the cookbook demo."""
from __future__ import annotations

import difflib
from typing import Sequence

from langchain_core.documents import Document


class SimpleReranker:
    """Approximate reranking using SequenceMatcher for demo purposes."""

    def __init__(self, top_n: int = 5) -> None:
        self.top_n = top_n

    def compress_documents(self, documents: Sequence[Document], query: str):
        if not documents:
            return []
        scored = []
        for doc in documents:
            score = difflib.SequenceMatcher(None, query.lower(), doc.page_content.lower()).ratio()
            doc.metadata["relevance_score"] = score
            scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[: self.top_n]]

