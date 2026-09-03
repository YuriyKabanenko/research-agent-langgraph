from langchain_core.tools import tool
from tavily import TavilyClient
import os

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def get_current_date() -> str:
    """Get the current date in format DD-MM-YY. Only call this if the response depends on knowing today's date."""
    from datetime import datetime
    today = datetime.now()
    return f"{today.day}-{today.month}-{today.year}"

@tool
def search_in_web(query: str) -> str:
    """
    Search the web for up-to-date information on the given query.

    Use this when the answer depends on current events, recent data, or facts
    that may not be present in your training data. Returns the top results as
    a formatted list of title, URL, and content snippet for each.

    Args:
        query: The search query, phrased like a search-engine query
            (keywords or a short question) rather than a full sentence.
    """
    response = tavily_client.search(query, max_results=3)
    results = response["results"]
    
    return "\n\n".join(
        f"{r['title']}\n{r['url']}\n{r['content']}" for r in results
    )

NAME_TO_TOOL = {
    "get_current_date": get_current_date,
    "search_in_web": search_in_web,
}
