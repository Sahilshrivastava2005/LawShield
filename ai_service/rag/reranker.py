from sentence_transformers import CrossEncoder

_reranker_model = None

def get_reranker():
    """Lazy load the BGE Reranker model."""
    global _reranker_model
    if _reranker_model is None:
        # BAAI/bge-reranker-base is highly effective for RAG
        _reranker_model = CrossEncoder('BAAI/bge-reranker-base', max_length=512)
    return _reranker_model

def rerank_documents(query: str, documents: list[str], top_k: int = 3) -> list[str]:
    """Rerank a list of documents based on relevance to the query."""
    if not documents:
        return []
        
    model = get_reranker()
    # CrossEncoder expects pairs of [query, document]
    pairs = [[query, doc] for doc in documents]
    
    # Predict scores
    scores = model.predict(pairs)
    
    # Sort documents by score (descending)
    scored_docs = list(zip(scores, documents))
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k documents
    return [doc for score, doc in scored_docs[:top_k]]
