"""
Supervisor node – routes the user request to the correct specialist agent.

Routing table
─────────────
planner     → full research pipeline (Planner → Research → Drafting → Citation → Review)
contract    → ContractReview agent
summarizer  → Summarizer agent
compliance  → Compliance agent
calculator  → Calculator agent
FINISH      → No further processing; ChatService will answer directly
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage

from graph.state import AgentState
from llm.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)

_VALID_ROUTES = {"planner", "contract", "summarizer", "compliance", "calculator", "FINISH"}


def supervisor_node(state: AgentState) -> dict:
    """Analyse the latest user message and pick the next agent."""
    model = get_llm_provider().get_model()

    # Use only the last human message to avoid leaking system/masking details
    last_human = next(
        (m.content for m in reversed(state["messages"]) if m.type == "human"),
        "",
    )

    prompt = f"""You are a Supervisor in a legal AI system.
Decide which specialist agent should handle the user's request.

Available routes:
- "planner"    → complex legal research, analysis, or advice
- "contract"   → review, compare, or draft a contract / clause
- "summarizer" → summarise a long legal text
- "compliance" → check whether a document meets regulatory requirements
- "calculator" → date deadlines, damages, capital gain, or any maths
- "FINISH"     → greeting, small-talk, or anything requiring a direct reply

Respond with ONLY valid JSON, e.g. {{"next": "planner"}}

User request: {last_human}
"""

    response = model.invoke([HumanMessage(content=prompt)])

    next_node = _parse_next(response.content)
    logger.info("Supervisor routed to: %s", next_node)
    return {"next_node": next_node}


def _parse_next(raw: str) -> str:
    try:
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

        next_node = data.get("next", "planner")
        if next_node not in _VALID_ROUTES:
            logger.warning("Supervisor returned unknown route %r – defaulting to planner", next_node)
            return "planner"
        return next_node
    except Exception as exc:
        logger.error("Failed to parse Supervisor response: %s", exc)
        return "planner"
