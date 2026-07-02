from typing import AsyncGenerator
from llm.providers.factory import get_llm_provider
from chat.history import get_session_history
from masking.masking_pipeline import mask_text, restore_text
from masking.replacement import MaskingState
from graph.graph import create_graph
from langchain_core.messages import HumanMessage, AIMessage
import re

class ChatService:
    def __init__(self, provider_name: str = None):
        self.provider_name = provider_name
        # Compile the multi-agent graph
        self.graph = create_graph()

    async def stream_chat(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Stream the execution steps of the LangGraph multi-agent system."""
        masked_message, masking_state = mask_text(message)
        
        # Initialize graph state
        state = {
            "messages": [HumanMessage(content=masked_message)],
            "plan": "",
            "research_data": [],
            "review_status": "",
            "next_node": ""
        }
        
        final_answer = None
        
        # Stream events from the graph
        async for event in self.graph.astream(state):
            for node_name, node_state in event.items():
                yield f"--- Executing Node: {node_name} ---\n"
                
                if node_name == "reviewer":
                    # Reviewer may or may not have approved; get its messages delta
                    msgs = node_state.get("messages", [])
                    if msgs:
                        final_answer = msgs[-1].content
                        
                elif node_name == "supervisor":
                    # When supervisor routes to END (FINISH), generate a direct response
                    next_node_val = node_state.get("next_node", "")
                    if next_node_val in ("FINISH", "__end__"):
                        # Generate a simple direct LLM response
                        model = get_llm_provider(self.provider_name).get_model()
                        direct_resp = model.invoke([HumanMessage(content=masked_message)])
                        final_answer = direct_resp.content
        
        if final_answer:
            restored = restore_text(final_answer, masking_state)
            yield f"\nFINAL ANSWER:\n{restored}\n"
        else:
            yield "\nFINAL ANSWER:\n(No response generated)\n"

    async def chat(self, session_id: str, message: str) -> str:
        """Non-streaming chat using LangGraph."""
        masked_message, masking_state = mask_text(message)
        
        state = {
            "messages": [HumanMessage(content=masked_message)],
            "plan": "",
            "research_data": [],
            "review_status": "",
            "next_node": ""
        }
        
        final_state = await self.graph.ainvoke(state)
        
        # Find the last AIMessage in the conversation (added by reviewer)
        messages = final_state.get("messages", [])
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        
        if ai_messages:
            final_msg = ai_messages[-1].content
        else:
            # Supervisor routed to END without going through reviewer — generate direct response
            model = get_llm_provider(self.provider_name).get_model()
            direct_resp = model.invoke([HumanMessage(content=masked_message)])
            final_msg = direct_resp.content
        
        return restore_text(final_msg, masking_state)
