"""
Self-RAG Evaluator.

Two checks:
1. grade_documents  – filters out irrelevant retrieved chunks before generation.
2. check_hallucination – verifies the final answer is grounded in the context.
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from llm.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)


def grade_documents(query: str, documents: list[str]) -> list[str]:
    """Return only documents that are relevant to the query."""
    model = get_llm_provider().get_model()
    relevant: list[str] = []

    for doc in documents:
        if not doc.strip():
            continue

        prompt = f"""You are a relevance grader.
Does the document below contain information that is useful for answering the question?
Answer with ONLY "yes" or "no".

Question: {query}
Document: {doc[:2000]}
"""
        try:
            response = model.invoke([HumanMessage(content=prompt)])
            if "yes" in response.content.strip().lower():
                relevant.append(doc)
        except Exception as exc:
            logger.warning("Document grading failed: %s – keeping document", exc)
            relevant.append(doc)  # Fail-safe: keep the document

    logger.info("Document grading: %d/%d chunks kept", len(relevant), len(documents))
    return relevant


def check_hallucination(generation: str, documents: list[str]) -> bool:
    """Return True if the generation is grounded in the documents."""
    if not documents:
        return True  # Nothing to compare against; assume grounded

    model = get_llm_provider().get_model()
    context = "\n---\n".join(d[:1000] for d in documents)  # cap context size

    prompt = f"""You are a hallucination detector.
Is the answer below fully supported by the provided facts?
Answer with ONLY "yes" (fully supported) or "no" (contains hallucinated claims).

Facts:
{context}

Answer: {generation[:2000]}
"""

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        result = "yes" in response.content.strip().lower()
        logger.info("Hallucination check result: %s", "grounded" if result else "HALLUCINATED")
        return result
    except Exception as exc:
        logger.warning("Hallucination check failed (%s); assuming grounded", exc)
        return True
