import logging
from fastapi import FastAPI
from dotenv import load_dotenv

# Load env variables before other imports
load_dotenv()

from chat.router import router as chat_router
from llm.router import router as llm_router
from document_processing.router import router as doc_router
from rag.router import router as rag_router

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Foundation API",
    description="Phase 1: Chatbot that can talk to an LLM",
    version="1.0.0"
)

# Include routers
app.include_router(chat_router)
app.include_router(llm_router)
app.include_router(doc_router)
app.include_router(rag_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Service...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
