from langchain_core.tools import tool
import difflib

@tool
def compare_documents(text_a: str, text_b: str) -> str:
    """
    Compares two text documents and returns a summary of the differences.
    Useful for comparing old vs new contracts or identifying modified clauses.
    Returns a unified diff format.
    """
    try:
        diff = list(difflib.unified_diff(
            text_a.splitlines(keepends=True),
            text_b.splitlines(keepends=True),
            fromfile='Document_A',
            tofile='Document_B',
            n=3
        ))
        if not diff:
            return "Documents are identical."
        
        return "".join(diff)
    except Exception as e:
        return f"Error comparing documents: {str(e)}"
