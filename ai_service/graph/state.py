from typing import TypedDict, List, Annotated, Optional
import operator
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The shared state of the multi-agent graph.

    Every field except ``messages`` is replaced (not appended) on each state
    update, which is LangGraph's default behaviour for plain fields.  The
    ``messages`` field uses ``operator.add`` so every node can safely append
    new messages without overwriting the list.
    """

    # Full conversation (system + history + new turn)
    messages: Annotated[List[BaseMessage], operator.add]

    # Routing decision made by the Supervisor
    next_node: str

    # ── Research pipeline fields ──────────────────────────────────────────────

    # Step-by-step resolution plan produced by Planner
    plan: str

    # Accumulated research snippets (one entry per Research iteration)
    research_data: List[str]

    # Draft produced by Drafting
    draft_content: str

    # Citations appended by Citation
    citations: List[str]

    # "approved" | "rejected" – set by Reviewer
    review_status: str

    # ── Specialised agent output fields ───────────────────────────────────────

    contract_analysis: str
    compliance_report: str
    summary: str
    calculation_result: str
