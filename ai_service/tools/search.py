from langchain_core.tools import tool
from rag.hybrid.search import advanced_hybrid_search

@tool
def legal_search(query: str, top_k: int = 5) -> str:
    """
    Search the internal legal database for case law, sections, or relevant documents.
    Provide a specific legal query. Returns matching text chunks separated by '---'.
    """
    try:
        retrieved_texts = advanced_hybrid_search(query, top_k=top_k)
        if not retrieved_texts:
            return "No relevant legal documents found."
        return "\n---\n".join(retrieved_texts)
    except Exception as e:
        return f"Error executing legal search: {str(e)}"
