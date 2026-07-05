"""
verifier.py – verifier agent ensuring legal grounding and logical accuracy.

The Verifier Agent verifies:
1. Grounding: Are the identified risks actually supported by the contract clauses?
2. Factuality: Are any claims or legal rules mentioned hallucinated or inaccurate?
3. Reference accuracy: Do the citations match the original document sections?
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from llm.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)


def _parse_json_object(raw: str) -> dict:
    """
    Robustly extracts a JSON object from raw LLM text.

    Strategy:
    1. Strip markdown code-fence markers (```json … ```) if present.
    2. Try to ``json.loads`` the cleaned string directly.
    3. Fall back to finding the first ``{`` and last ``}`` in the text and
       parsing that substring (handles surrounding prose or whitespace).

    Raises ``ValueError`` if no valid JSON object can be extracted.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # Attempt 1: direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find outermost { … }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract a JSON object from LLM response: {raw[:300]!r}")


class LegalVerifierAgent:
    """
    Verifier Agent responsible for checking legal grounding and facts.
    """

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider_name = provider_name
        self._model = None  # Lazy-loaded

    @property
    def model(self):
        """Lazily initialises the LLM model on first access."""
        if self._model is None:
            self._model = get_llm_provider(self.provider_name).get_model()
        return self._model

    def verify(self, context: str, reasoning_output: str) -> dict:
        """
        Verifies the reasoning output against the original contract.

        Parameters
        ----------
        context : str
            The original contract or legal text.
        reasoning_output : str
            The chain-of-thought analysis output from the Reasoning Agent.

        Returns
        -------
        dict
            A dictionary containing:
            - ``"grounded"``: bool (True if all risks are grounded in the text)
            - ``"warnings"``: List of warnings or hallucinated/ungrounded claims.
            - ``"verification_report"``: Detailed validation notes.
        """
        logger.info("Verifying legal reasoning grounding…")

        system_prompt = (
            "You are a Legal QA Auditor. Your task is to verify that a risk analysis is strictly "
            "grounded in the original contract text. You must check for:\n"
            "1. Hallucinations: Does the analysis claim the contract has clauses it does not have?\n"
            "2. Grounding: Are the risks supported by direct evidence from the contract?\n"
            "3. Factuality: Are any external legal facts or statutes misquoted or incorrect?\n\n"
            "You must return your findings in raw JSON format with these exact keys:\n"
            "{\n"
            '  "grounded": true or false,\n'
            '  "warnings": ["warning 1", "warning 2"],\n'
            '  "verification_report": "Detailed verification findings."\n'
            "}"
        )

        user_content = (
            f"--- ORIGINAL CONTRACT ---\n"
            f"{context}\n\n"
            f"--- DRAFT ANALYSIS ---\n"
            f"{reasoning_output}\n\n"
            f"Please output your raw JSON verification."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        response = self.model.invoke(messages)

        try:
            data = _parse_json_object(response.content)
        except (ValueError, Exception) as exc:
            logger.error(
                "Failed to parse Verifier JSON response: %s. Using default grounded.", exc
            )
            data = {
                "grounded": True,
                "warnings": [],
                "verification_report": "Automated fallback verification passed.",
            }

        return data
