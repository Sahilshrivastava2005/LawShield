from graph.state import AgentState
from typing import Literal

def route_supervisor(state: AgentState) -> Literal["planner", "__end__"]:
    """Route based on Supervisor's decision."""
    next_node = state.get("next_node")
    if next_node == "FINISH" or next_node == "__end__":
        return "__end__"
    return "planner"

def route_reviewer(state: AgentState) -> Literal["planner", "__end__"]:
    """Route based on Reviewer's status."""
    status = state.get("review_status", "approved")
    # To prevent infinite loops in this simple example, we limit rejection count in a real app.
    # For phase 5 demo, if rejected, send back to planner.
    if status == "rejected":
        # Check if we've looped too much (based on research data size)
        if len(state.get("research_data", [])) < 3:
            return "planner"
    return "__end__"
