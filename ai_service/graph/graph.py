from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes.supervisor import supervisor_node
from graph.nodes.planner import planner_node
from graph.nodes.research import research_node
from graph.nodes.reviewer import reviewer_node
from graph.conditions.routing import route_supervisor, route_reviewer

def create_graph():
    """Compiles and returns the multi-agent state graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # Add edges
    workflow.set_entry_point("supervisor")
    
    # Supervisor conditionally routes to planner or END
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {"planner": "planner", "__end__": END}
    )
    
    # Planner goes to Research
    workflow.add_edge("planner", "research")
    
    # Research goes to Reviewer
    workflow.add_edge("research", "reviewer")
    
    # Reviewer conditionally goes back to Planner or END
    workflow.add_conditional_edges(
        "reviewer",
        route_reviewer,
        {"planner": "planner", "__end__": END}
    )
    
    return workflow.compile()
