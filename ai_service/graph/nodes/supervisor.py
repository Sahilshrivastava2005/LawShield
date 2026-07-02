from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from llm.providers.factory import get_llm_provider
import json
import re

def supervisor_node(state: AgentState) -> dict:
    """
    Analyzes the request and determines the next step.
    For simplicity, it delegates to 'planner'.
    """
    model = get_llm_provider().get_model()
    
    prompt = f"""You are a Supervisor agent.
Your job is to determine if the user's request requires a research plan.
Return a JSON object with a 'next' key, which must be 'planner' or 'FINISH'.
If it's a simple greeting, return 'FINISH'. Otherwise, return 'planner'.

Messages:
{[m.content for m in state['messages']]}
"""
    response = model.invoke([HumanMessage(content=prompt)])
    
    try:
        # Extract JSON object robustly (handles markdown fences and extra text)
        raw = response.content
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
        next_node = data.get("next", "planner")
    except Exception:
        next_node = "planner"
        
    return {"next_node": next_node}
