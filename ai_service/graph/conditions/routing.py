from graph.state import AgentState
from typing import Literal

def route_supervisor(state: AgentState) -> Literal["planner", "contract", "summarizer", "compliance", "calculator", "reasoning", "__end__"]:
    """Route based on Supervisor's decision."""
    next_node = state.get("next_node")
    if next_node == "FINISH" or next_node == "__end__":
        return "__end__"
    if next_node in ["contract", "summarizer", "compliance", "calculator", "reasoning"]:
        return next_node
    return "planner"

def route_reviewer(state: AgentState) -> Literal["planner", "__end__"]:
    """Route based on Reviewer's status."""
    status = state.get("review_status", "approved")
    # For phase 6 demo, if rejected, send back to planner.
    if status == "rejected":
        # Limit rejection count to avoid infinite loops
        if len(state.get("research_data", [])) < 3:
            return "planner"
    return "__end__"
