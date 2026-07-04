"""
Memory – Long-Term Fact Store.

Facts are extracted from each completed exchange and stored in-process.
In production replace _long_term_facts with a PostgreSQL / MongoDB collection.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Dict, List

from langchain_core.messages import HumanMessage

from llm.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)

# In-process store: session_id → list of fact strings
_long_term_facts: Dict[str, List[str]] = {}

_MAX_FACTS = 25  # cap per session to avoid prompt bloat


def extract_and_save_facts(session_id: str, exchange: str) -> None:
    """Extract persistent facts from a user-AI exchange and save them."""
    model = get_llm_provider().get_model()

    prompt = f"""You are a Memory Extraction agent.
Read the following conversation exchange and extract any long-term facts about:
- The user's role, clients, or ongoing cases
- User preferences (e.g. "User prefers bullet-point summaries")
- Any key legal entities mentioned (people, companies, jurisdictions)

Return a JSON list of short fact strings.  Return [] if nothing notable was found.

Conversation:
{exchange}
"""

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        raw = response.content

        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            facts: List[str] = json.loads(match.group())
        else:
            cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
            facts = json.loads(cleaned)

        if not isinstance(facts, list):
            return

        if session_id not in _long_term_facts:
            _long_term_facts[session_id] = []

        # Deduplicate and cap
        existing = set(_long_term_facts[session_id])
        new_facts = [f for f in facts if isinstance(f, str) and f not in existing]
        combined = _long_term_facts[session_id] + new_facts
        _long_term_facts[session_id] = combined[-_MAX_FACTS:]
        logger.debug("Saved %d new long-term facts for session %s", len(new_facts), session_id)

    except Exception as exc:
        logger.warning("Failed to extract long-term facts: %s", exc)


def get_long_term_facts(session_id: str) -> str:
    """Return a formatted string for injection into the system prompt."""
    facts = _long_term_facts.get(session_id, [])
    if not facts:
        return ""
    lines = "\n".join(f"- {f}" for f in facts)
    return f"Long-term facts about this user:\n{lines}"
