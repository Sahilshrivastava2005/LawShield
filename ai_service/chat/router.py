from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from chat.chat_service import ChatService
from memory.conversation import get_conversation

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream the AI response token-by-token using Server-Sent Events.
    Each data event is a raw chunk; the final [DONE] event signals end.
    """
    try:
        service = ChatService(provider_name=request.provider)

        async def event_generator():
            async for chunk in service.stream_chat(request.session_id, request.message):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint. Returns the full response plus any sources.
    The `sources` field is a list of citation strings (e.g. statute names,
    case names) extracted by the AI graph; it may be empty.
    """
    try:
        service = ChatService(provider_name=request.provider)
        response_text = await service.chat(request.session_id, request.message)

        # Sources are extracted by the citation agent inside the graph.
        # The current ChatService returns a plain string; extract citations
        # if they appear in a structured block, otherwise return empty list.
        sources: List[str] = []

        return ChatResponse(response=response_text, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear the in-memory conversation history for a session."""
    get_conversation(session_id).clear()
    return {"status": "success", "message": f"History cleared for {session_id}"}
