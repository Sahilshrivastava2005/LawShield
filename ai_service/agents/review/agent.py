from langchain_core.messages import HumanMessage, AIMessage
from graph.state import AgentState
from llm.providers.factory import get_llm_provider
import json
import re

def review_node(state: AgentState) -> dict:
    """Reviews the final drafted and cited content against the plan and request."""
    model = get_llm_provider().get_model()
    
    plan = state.get("plan", "")
    draft = state.get("draft_content", "")
    user_req = state["messages"][0].content if state["messages"] else ""
    
    prompt = f"""You are a Legal Reviewer agent.
Review the following drafted response against the original request and plan.
Determine if it fully answers the user's request and is legally sound.
Return a JSON object with a 'status' key (must be 'approved' or 'rejected') and a 'final_answer' key containing the synthesized final response to the user.

Request: {user_req}
Plan: {plan}
Drafted Response: {draft}
"""
    
    response = model.invoke([HumanMessage(content=prompt)])
    
    try:
        # Extract JSON robustly
        raw = response.content
        cleaned = raw.strip()
        for fence in ["```json", "```"]:
            cleaned = cleaned.replace(fence, "")
        cleaned = cleaned.strip()
        
        start = cleaned.find('{')
        if start != -1:
            depth = 0
            end = start
            for i, ch in enumerate(cleaned[start:], start=start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                if depth == 0:
                    end = i
                    break
            data = json.loads(cleaned[start:end + 1])
        else:
            data = json.loads(cleaned)
        
        status = data.get("status", "approved")
        final_answer = data.get("final_answer", draft)
    except Exception:
        # Fallback: treat the full response as the final answer
        status = "approved"
        final_answer = response.content
        
    return {
        "review_status": status,
        # Append the final answer to messages to return to the user
        "messages": [AIMessage(content=final_answer)]
    }
