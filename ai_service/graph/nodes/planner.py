from langchain_core.messages import HumanMessage
from graph.state import AgentState
from llm.providers.factory import get_llm_provider

def planner_node(state: AgentState) -> dict:
    """Generates a research plan based on the user's request."""
    model = get_llm_provider().get_model()
    
    # Extract latest user request
    user_req = state["messages"][-1].content if state["messages"] else ""
    
    prompt = f"""You are a legal Planner agent.
Create a step-by-step research plan to answer the following request.
Keep it concise.

Request: {user_req}
"""
    
    response = model.invoke([HumanMessage(content=prompt)])
    
    # Store the plan in the state
    return {"plan": response.content}
