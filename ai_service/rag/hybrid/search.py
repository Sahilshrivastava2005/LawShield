"""
Advanced Hybrid Search – combines Qdrant dense vectors with ES BM25 lexical search.

Reciprocal Rank Fusion (RRF) is used to merge the two result lists.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_K = 60  # RRF constant


def _rrf_score(rank: int) -> float:
    return 1.0 / (_K + rank + 1)


def advanced_hybrid_search(
    query: str,
    collection_name: str = "documents",
    top_k: int = 10,
    metadata_filter: Optional[dict] = None,
) -> list[str]:
    """Return de-duplicated, RRF-merged text chunks from Qdrant + Elasticsearch."""

    qdrant_results: list[str] = []
    es_results: list[str] = []

    # ── 1. Dense (Qdrant) ─────────────────────────────────────────────────────
    try:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue
        from rag.embedding import get_embeddings
        from rag.retrieval import get_qdrant_client

        q_client = get_qdrant_client()
        query_vector = get_embeddings().embed_query(query)

        q_filter = None
        if metadata_filter:
            conditions = [
                FieldCondition(key=f"metadata.{k}", match=MatchValue(value=v))
                for k, v in metadata_filter.items()
            ]
            q_filter = Filter(must=conditions)

        response = q_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=q_filter,
            limit=top_k,
        )
        qdrant_results = [
            r.payload.get("text", "") for r in response.points if r.payload.get("text")
        ]
    except Exception as exc:
        logger.error("Qdrant search error: %s", exc)

    # ── 2. Sparse (Elasticsearch BM25) ────────────────────────────────────────
    try:
        from rag.retrieval import get_es_client

        es_client = get_es_client()

        must_clauses: list[dict] = [{"match": {"text": query}}]
        if metadata_filter:
            for k, v in metadata_filter.items():
                must_clauses.append({"match": {f"metadata.{k}": v}})

        es_response = es_client.search(
            index=collection_name,
            body={"query": {"bool": {"must": must_clauses}}, "size": top_k},
        )
        es_results = [
            hit["_source"].get("text", "")
            for hit in es_response["hits"]["hits"]
            if hit["_source"].get("text")
        ]
    except Exception as exc:
        logger.error("Elasticsearch search error: %s", exc)

    # ── 3. Reciprocal Rank Fusion ─────────────────────────────────────────────
    scores: dict[str, float] = {}

    for rank, text in enumerate(qdrant_results):
        scores[text] = scores.get(text, 0.0) + _rrf_score(rank)

    for rank, text in enumerate(es_results):
        scores[text] = scores.get(text, 0.0) + _rrf_score(rank)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [text for text, _ in ranked[:top_k]]
