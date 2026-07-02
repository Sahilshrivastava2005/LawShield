from langchain_core.messages import HumanMessage
from graph.state import AgentState
from llm.providers.factory import get_llm_provider
from rag.retrieval import hybrid_search

def research_node(state: AgentState) -> dict:
    """Executes the research plan using the RAG pipeline."""
    model = get_llm_provider().get_model()
    
    plan = state.get("plan", "")
    user_req = state["messages"][-1].content if state["messages"] else ""
    
    # In a real scenario, the Researcher would extract keywords from the plan to search Qdrant/ES.
    # We will run a simple hybrid search based on the user's original query for demonstration.
    try:
        retrieved_texts = hybrid_search(user_req, top_k=5)
        context = "\n---\n".join(retrieved_texts)
    except Exception:
        context = "No documents found."
        
    prompt = f"""You are a Researcher agent.
Execute the following plan using the provided context from our legal databases.

Plan:
{plan}

Context:
{context}

Original Request: {user_req}

Write your detailed research findings.
"""
    
    response = model.invoke([HumanMessage(content=prompt)])
    
    # Append new research to existing research data
    existing_research = state.get("research_data", [])
    if existing_research is None:
        existing_research = []
        
    return {"research_data": existing_research + [response.content]}
