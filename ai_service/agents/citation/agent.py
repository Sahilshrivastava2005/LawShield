"""
Citation node – formats and appends Bluebook citations to the draft.
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, ToolMessage

from graph.state import AgentState
from llm.providers.factory import get_llm_provider
from tools.citation import format_citation

logger = logging.getLogger(__name__)

_TOOLS = [format_citation]
_TOOL_MAP = {t.name: t for t in _TOOLS}


def citation_node(state: AgentState) -> dict:
    """Add properly formatted legal citations to the draft."""
    base_model = get_llm_provider().get_model()
    model = base_model.bind_tools(_TOOLS)

    draft = state.get("draft_content", "")
    research = (state.get("research_data") or [""])[-1]

    prompt = f"""You are a Legal Citation specialist.
Review the draft below and the research it was based on.
Use the format_citation tool to format any case references found in the research into Bluebook style.
Return the COMPLETE updated draft with citations appended at the end.

Research:
{research}

Draft:
{draft}
"""

    ai_msg = model.invoke([HumanMessage(content=prompt)])
    extra_messages = [ai_msg]
    citation_list: list[str] = []

    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        for tc in ai_msg.tool_calls:
            tool_fn = _TOOL_MAP.get(tc["name"])
            try:
                result = tool_fn.invoke(tc["args"]) if tool_fn else f"Unknown tool: {tc['name']}"
                citation_list.append(str(result))
            except Exception as exc:
                result = f"Tool error: {exc}"
            extra_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        synthesis = model.invoke([HumanMessage(content=prompt)] + extra_messages)
        cited_draft = synthesis.content
    else:
        cited_draft = ai_msg.content

    logger.info("Citation completed; %d citations added", len(citation_list))
    return {"draft_content": cited_draft, "citations": citation_list}
