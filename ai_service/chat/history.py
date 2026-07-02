from typing import Dict
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

# Simple in-memory store mapping session_id to chat history
_store: Dict[str, BaseChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create chat history for a given session ID."""
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]

def clear_session_history(session_id: str):
    """Clear chat history for a session."""
    if session_id in _store:
        _store[session_id].clear()
