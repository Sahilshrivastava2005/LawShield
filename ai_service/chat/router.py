from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

from chat.chat_service import ChatService
from memory.conversation import get_conversation

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: str | None = None

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    try:
        service = ChatService(provider_name=request.provider)
        
        async def event_generator():
            async for chunk in service.stream_chat(request.session_id, request.message):
                # Simple SSE format
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def chat(request: ChatRequest):
    try:
        service = ChatService(provider_name=request.provider)
        response = await service.chat(request.session_id, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    get_conversation(session_id).clear()
    return {"status": "success", "message": f"History cleared for {session_id}"}

