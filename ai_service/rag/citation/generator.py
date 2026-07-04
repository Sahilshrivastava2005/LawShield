from llm.providers.factory import get_llm_provider
from langchain_core.messages import HumanMessage

def generate_citations(generation: str, documents: list[str]) -> str:
    """Appends citations mapping the generated text to the source documents."""
    model = get_llm_provider().get_model()
    context = "\n---\n".join([f"[Doc {i+1}]: {doc}" for i, doc in enumerate(documents)])
    
    prompt = f"""You are a citation agent.
Review the following answer and the source documents.
Append a 'Citations' section to the end of the answer linking claims to the specific [Doc X].
Do not change the original answer text.

Source Documents:
{context}

Answer:
{generation}
"""
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content
