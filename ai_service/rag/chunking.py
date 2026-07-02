from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_text_splitter():
    """Returns a pre-configured text splitter for document chunking."""
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

def chunk_text(text: str, metadata: dict = None) -> list:
    """Split text into overlapping chunks."""
    if not metadata:
        metadata = {}
    splitter = get_text_splitter()
    return splitter.create_documents([text], metadatas=[metadata])
