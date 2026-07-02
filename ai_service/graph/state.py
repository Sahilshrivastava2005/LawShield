from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """The state of the multi-agent graph."""
    # List of messages representing the conversation history
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Current research plan
    plan: str
    
    # Collected research data
    research_data: List[str]
    
    # Review status (e.g., "approved", "rejected")
    review_status: str
    
    # The next node to route to (set by Supervisor/Conditions)
    next_node: str
