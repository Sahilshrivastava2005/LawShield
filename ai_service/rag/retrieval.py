from qdrant_client import QdrantClient
from elasticsearch import Elasticsearch
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Singletons for clients
_qdrant_client = None
_es_client = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    return _qdrant_client

def get_es_client() -> Elasticsearch:
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(settings.ELASTICSEARCH_URL)
    return _es_client

def init_collections(collection_name: str = "documents"):
    """Initialize collections in Qdrant and indices in ES."""
    q_client = get_qdrant_client()
    es_client = get_es_client()
    
    # Init Qdrant (assume 1024 dims for BAAI/bge-large-en-v1.5)
    try:
        from qdrant_client.http.models import VectorParams, Distance
        collections = [c.name for c in q_client.get_collections().collections]
        if collection_name not in collections:
            q_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")

    # Init Elasticsearch index
    try:
        if not es_client.indices.exists(index=collection_name):
            es_client.indices.create(
                index=collection_name,
                body={
                    "mappings": {
                        "properties": {
                            "text": {"type": "text"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
            )
            logger.info(f"Created ES index: {collection_name}")
    except Exception as e:
        logger.error(f"Error initializing Elasticsearch: {e}")

def hybrid_search(query: str, collection_name: str = "documents", top_k: int = 10, metadata_filter: dict = None) -> list:
    """
    Perform a simple hybrid search.
    In a real system, you'd use Reciprocal Rank Fusion (RRF) to combine results.
    For this phase, we will fetch from both and return unique text chunks for the reranker.
    """
    results = set()
    
    # 1. Vector Search (Qdrant)
    try:
        from rag.embedding import get_embeddings
        q_client = get_qdrant_client()
        query_vector = get_embeddings().embed_query(query)
        
        # Build Qdrant filter
        q_filter = None
        if metadata_filter:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            conditions = [
                FieldCondition(key=f"metadata.{k}", match=MatchValue(value=v))
                for k, v in metadata_filter.items()
            ]
            q_filter = Filter(must=conditions)
            
        qdrant_response = q_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=q_filter,
            limit=top_k
        )
        for r in qdrant_response.points:
            results.add(r.payload.get("text", ""))
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")

    # 2. Lexical Search (Elasticsearch)
    try:
        es_client = get_es_client()
        
        must_clauses = [{"match": {"text": query}}]
        if metadata_filter:
            for k, v in metadata_filter.items():
                must_clauses.append({"match": {f"metadata.{k}": v}})
                
        es_query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": top_k
        }
        
        es_results = es_client.search(index=collection_name, body=es_query)
        for hit in es_results['hits']['hits']:
            results.add(hit['_source'].get("text", ""))
    except Exception as e:
        logger.error(f"ES search error: {e}")

    return list(results)
