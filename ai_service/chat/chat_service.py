"""
ChatService – orchestrates the multi-agent graph with full memory integration.
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from graph.graph import create_graph
from llm.providers.factory import get_llm_provider
from masking.masking_pipeline import mask_text, restore_text
from memory.conversation import SlidingWindowMemory, get_conversation
from memory.long_term import extract_and_save_facts, get_long_term_facts
from memory.vector import save_to_vector_memory, search_vector_memory

logger = logging.getLogger(__name__)

# Nodes that place a finished answer in ``state["messages"]``
_TERMINAL_NODES = {"review", "contract", "compliance", "summarizer", "calculator"}

# Default blank state (keeps keys consistent with AgentState)
_BLANK_STATE = {
    "messages": [],
    "next_node": "",
    "plan": "",
    "research_data": [],
    "draft_content": "",
    "citations": [],
    "review_status": "",
    "contract_analysis": "",
    "compliance_report": "",
    "summary": "",
    "calculation_result": "",
}


class ChatService:
    """Wraps the LangGraph multi-agent workflow with masking and memory."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider_name = provider_name
        self.graph = create_graph()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_system_message(self, session_id: str, masked_query: str) -> SystemMessage:
        """Compose the system prompt enriched with long-term and vector memory."""
        base = "You are Harvey, a highly advanced legal AI assistant. Be concise, accurate, and cite your sources."

        facts = get_long_term_facts(session_id)
        if facts:
            base += f"\n\n{facts}"

        past = search_vector_memory(session_id, masked_query, top_k=2)
        if past:
            base += f"\n\nRelevant past conversations:\n{past}"

        return SystemMessage(content=base)

    def _prepare_state(self, session_id: str, masked_query: str) -> tuple[dict, SlidingWindowMemory, HumanMessage]:
        """Build the initial graph state and update conversation memory."""
        sys_msg = self._build_system_message(session_id, masked_query)

        convo = get_conversation(session_id)
        user_msg = HumanMessage(content=masked_query)
        convo.add_message(user_msg)

        messages = [sys_msg] + convo.get_messages()

        state = {**_BLANK_STATE, "messages": messages}
        return state, convo, user_msg

    def _commit_memory_background(
        self, session_id: str, convo: SlidingWindowMemory, user_msg: HumanMessage, answer: str
    ) -> None:
        """Save the exchange to memory asynchronously (fire-and-forget)."""
        ai_msg = AIMessage(content=answer)
        convo.add_message(ai_msg)

        exchange = f"User: {user_msg.content}\nHarvey: {answer}"

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(asyncio.to_thread(extract_and_save_facts, session_id, exchange))
            loop.create_task(asyncio.to_thread(save_to_vector_memory, session_id, [user_msg, ai_msg]))
        except RuntimeError:
            # No running event loop (e.g., called from sync test)
            extract_and_save_facts(session_id, exchange)
            save_to_vector_memory(session_id, [user_msg, ai_msg])

    def _direct_response(self, messages: list) -> str:
        """Ask the LLM directly (Supervisor chose FINISH)."""
        model = get_llm_provider(self.provider_name).get_model()
        return model.invoke(messages).content

    # ── public API ────────────────────────────────────────────────────────────

    async def stream_chat(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Stream node-by-node progress then yield the final answer."""
        masked_message, masking_state = mask_text(message)
        state, convo, user_msg = self._prepare_state(session_id, masked_message)
        messages = state["messages"]

        final_answer: str | None = None

        async for event in self.graph.astream(state):
            for node_name, node_state in event.items():
                yield f"data: [Node: {node_name}]\n\n"

                if node_name in _TERMINAL_NODES:
                    msgs = node_state.get("messages") or []
                    if msgs:
                        final_answer = msgs[-1].content

                elif node_name == "supervisor":
                    if node_state.get("next_node") in ("FINISH", "__end__"):
                        final_answer = self._direct_response(messages)

        if not final_answer:
            final_answer = "(No response generated)"

        self._commit_memory_background(session_id, convo, user_msg, final_answer)
        restored = restore_text(final_answer, masking_state)
        yield f"data: [FINAL]\n\n"
        yield f"data: {restored}\n\n"
        yield "data: [DONE]\n\n"

    async def chat(self, session_id: str, message: str) -> str:
        """Non-streaming chat; returns the final text response."""
        masked_message, masking_state = mask_text(message)
        state, convo, user_msg = self._prepare_state(session_id, masked_message)
        messages = state["messages"]

        final_state = await self.graph.ainvoke(state)

        all_messages = final_state.get("messages") or []
        ai_messages = [m for m in all_messages if isinstance(m, AIMessage)]

        if ai_messages:
            final_msg = ai_messages[-1].content
        else:
            final_msg = self._direct_response(messages)

        self._commit_memory_background(session_id, convo, user_msg, final_msg)
        return restore_text(final_msg, masking_state)
