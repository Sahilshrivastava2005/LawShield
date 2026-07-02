from langchain_core.documents import Document
from rag.chunking import chunk_text
from rag.embedding import get_embeddings
from rag.retrieval import get_qdrant_client, get_es_client, hybrid_search, init_collections
from rag.reranker import rerank_documents
import uuid
import logging

logger = logging.getLogger(__name__)

def ingest_document(text: str, metadata: dict, collection_name: str = "documents"):
    """Pipeline to chunk, embed, and index a document into Qdrant & ES."""
    init_collections(collection_name)
    
    # 1. Chunking
    chunks = chunk_text(text, metadata)
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    
    # 2. Embeddings
    logger.info("Generating embeddings...")
    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(texts)
    
    # Generate UUIDs
    point_ids = [str(uuid.uuid4()) for _ in texts]
    
    # 3. Index to Qdrant (Vector)
    try:
        from qdrant_client.http.models import PointStruct
        q_client = get_qdrant_client()
        points = [
            PointStruct(id=pid, vector=vec, payload={"text": txt, "metadata": meta})
            for pid, vec, txt, meta in zip(point_ids, vectors, texts, metadatas)
        ]
        q_client.upsert(collection_name=collection_name, points=points)
    except Exception as e:
        logger.error(f"Failed to ingest to Qdrant: {e}")

    # 4. Index to Elasticsearch (Lexical)
    try:
        es_client = get_es_client()
        operations = []
        for pid, txt, meta in zip(point_ids, texts, metadatas):
            operations.append({"index": {"_index": collection_name, "_id": pid}})
            operations.append({"text": txt, "metadata": meta})
            
        if operations:
            es_client.bulk(operations=operations)
    except Exception as e:
        logger.error(f"Failed to ingest to ES: {e}")

    return {"status": "success", "chunks_indexed": len(texts)}

async def ask_question_pipeline(query: str, metadata_filter: dict = None, collection_name: str = "documents"):
    """Pipeline to retrieve, rerank, and generate an answer using the Chat module."""
    # 1. Retrieve (Hybrid Search)
    retrieved_texts = hybrid_search(query, collection_name, top_k=15, metadata_filter=metadata_filter)
    
    # 2. Rerank
    top_docs = rerank_documents(query, retrieved_texts, top_k=3)
    
    context = "\n\n---\n\n".join(top_docs)
    
    # 3. Generate Answer (using ChatService)
    from chat.chat_service import ChatService
    service = ChatService()
    
    # Override standard prompt to include context
    prompt = f"""
Use the following context to answer the user's question. If you don't know the answer, just say you don't know.
Context:
{context}

Question: {query}
"""
    # For a real app, you would pass a session ID from the user
    session_id = "rag_session_" + str(uuid.uuid4())
    response = await service.chat(session_id, prompt)
    
    return {
        "answer": response,
        "context_used": top_docs
    }
