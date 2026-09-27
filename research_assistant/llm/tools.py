import contextvars
import os

from langchain_core.tools import tool
from tavily import TavilyClient

from . import mock

# Per-agent BYOK Tavily key, set by AgentService around the graph run - same reasoning
# as the LLM key in model.py (kept out of state, so out of traces and checkpoints).
#
# Unlike the LLM key, "set to None" and "never set" mean different things here: the
# server always sets it (None when the agent has no key), and then the env var is
# never consulted - so a deployed server can't silently fall back to the operator's
# own TAVILY_API_KEY and spend their credits. Only a caller that never set it at all
# (the CLIs) falls back to the env var.
_UNSET = object()
_tavily_key_var: contextvars.ContextVar = contextvars.ContextVar(
    "research_assistant_tavily_key", default=_UNSET
)


def set_tavily_api_key(api_key: str | None) -> contextvars.Token:
    return _tavily_key_var.set(api_key)


def reset_tavily_api_key(token: contextvars.Token) -> None:
    _tavily_key_var.reset(token)


def _resolve_tavily_key() -> str | None:
    key = _tavily_key_var.get()
    return os.getenv("TAVILY_API_KEY") if key is _UNSET else key

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
    if mock.web_search_mocked():
        # MOCK_WEB_SEARCH: canned results, no Tavily key or credits needed (llm/mock.py).
        return mock.mock_search(query)

    try:
        # Built per call because the key is per agent. Construction is cheap (no
        # network), and a missing key raises here, inside the try, like any other failure.
        response = TavilyClient(api_key=_resolve_tavily_key()).search(query, max_results=3)
    except Exception as e:
        # Quota exhausted, bad/missing key, network down, ... - ToolNode would re-raise this and
        # crash the whole research run, throwing away everything already paid for.
        # Tell the model instead, and discourage it from burning more rounds retrying.
        # Only the exception type goes back: the message could contain request details.
        return (
            f"Web search is unavailable ({type(e).__name__}). Do not call this tool "
            "again; continue with the information you already have."
        )

    results = response["results"]

    if not results:
        # An empty string here becomes an empty tool_result content block, which
        # Anthropic's API rejects outright ("user messages must have non-empty
        # content") - give the model something to read instead.
        return "No results found for this query."

    return "\n\n".join(
        f"{r['title']}\n{r['url']}\n{r['content']}" for r in results
    )
