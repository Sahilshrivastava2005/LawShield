from langchain_core.tools import tool
import urllib.request
import urllib.parse
import json

@tool
def web_search(query: str, max_results: int = 3) -> str:
    """
    Perform a live web search using a free search API (like DuckDuckGo or similar).
    This allows agents to find up-to-date public information.
    For this phase, this wraps a public search endpoint.
    """
    try:
        # For demonstration without external API keys, we use a simple fallback or mock.
        # In a real app, you would use langchain_community.tools.tavily_search or duckduckgo
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            search = DuckDuckGoSearchRun()
            return search.invoke(query)
        except ImportError:
            return f"Mock Search Result for '{query}': Current laws or regulations are constantly evolving. Please ensure `duckduckgo-search` is installed for real results."
    except Exception as e:
        return f"Error executing web search: {str(e)}"
