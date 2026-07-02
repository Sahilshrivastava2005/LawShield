from langchain_huggingface import HuggingFaceEmbeddings

# Cache the embeddings model so it is only loaded once
_embeddings_model = None

def get_embeddings():
    """Lazy load the BGE embedding model."""
    global _embeddings_model
    if _embeddings_model is None:
        # BAAI/bge-large-en-v1.5 is a top-tier open source embedding model
        model_name = "BAAI/bge-large-en-v1.5"
        model_kwargs = {'device': 'cpu'}  # Change to 'cuda' or 'mps' if GPU available
        encode_kwargs = {'normalize_embeddings': True} # BGE models require normalized embeddings
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
    return _embeddings_model
