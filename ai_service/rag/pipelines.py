from langchain_core.documents import Document
from rag.chunking import chunk_text
from rag.embedding import get_embeddings
from rag.retrieval import get_qdrant_client, get_es_client, init_collections
from rag.reranker import rerank_documents
import uuid
import logging

from rag.adaptive.router import route_query
from rag.adaptive.query_rewrite import rewrite_query
from rag.metadata.filters import extract_metadata_filters
from rag.hybrid.search import advanced_hybrid_search
from rag.self_rag.evaluator import grade_documents, check_hallucination
from rag.citation.generator import generate_citations

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
    """Advanced RAG Pipeline."""
    
    # 1. Adaptive Routing
    source = route_query(query)
    
    if source == "direct":
        # Answer directly without RAG
        from chat.chat_service import ChatService
        service = ChatService()
        response = await service.chat("direct_" + str(uuid.uuid4()), query)
        return {"answer": response, "context_used": []}
    
    if source == "web_search":
        from tools.web import web_search
        web_results = web_search.invoke(query)
        context = [web_results]
    else:
        # 2. Query Rewrite
        optimized_query = rewrite_query(query)
        
        # 3. Metadata Filtering
        extracted_filters = extract_metadata_filters(query)
        if metadata_filter:
            extracted_filters.update(metadata_filter)
            
        # 4. Hybrid Search
        retrieved_texts = advanced_hybrid_search(
            query=optimized_query, 
            collection_name=collection_name, 
            top_k=15, 
            metadata_filter=extracted_filters
        )
        
        # 5. Reranking
        top_docs = rerank_documents(optimized_query, retrieved_texts, top_k=5)
        
        # 6. Self-RAG (Document Relevance)
        relevant_docs = grade_documents(optimized_query, top_docs)
        if not relevant_docs:
            return {"answer": "I could not find relevant internal documents to answer your question.", "context_used": []}
            
        context = relevant_docs

    context_str = "\n\n---\n\n".join(context)
    
    # 7. Generate Answer
    from chat.chat_service import ChatService
    service = ChatService()
    
    prompt = f"""Use the following context to answer the user's question. If you don't know the answer, just say you don't know.
Context:
{context_str}

Question: {query}
"""
    session_id = "adv_rag_session_" + str(uuid.uuid4())
    generation = await service.chat(session_id, prompt)
    
    # 8. Self-RAG (Hallucination Check)
    if source != "web_search":
        is_grounded = check_hallucination(generation, context)
        if not is_grounded:
            # Simple retry logic, normally handled by LangGraph
            generation = await service.chat(session_id, f"Your previous answer contained hallucinations. Please strictly use this context:\n{context_str}\n\nQuestion: {query}")
            
    # 9. Citation Generation
    if source != "web_search":
        final_answer = generate_citations(generation, context)
    else:
        final_answer = generation
    
    return {
        "answer": final_answer,
        "context_used": context
    }
