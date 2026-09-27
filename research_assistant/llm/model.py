import contextvars
import os
from functools import lru_cache

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel
from typing_extensions import TypedDict, Annotated
from research_assistant.state import ModelFamily
from . import tools

DEFAULT_MODEL_FAMILY = ModelFamily.anthropic
DEFAULT_MODEL_NAME = "claude-haiku-4-5-20251001"

def _tools(web_search: bool) -> list:
    # get_current_date is free; search_in_web spends the agent's own Tavily credits, so
    # it's only offered to the model when the agent has web search enabled.
    return [tools.get_current_date, tools.search_in_web] if web_search else [tools.get_current_date]

# Per-agent BYOK token, set by AgentService.invoke() around the graph run and read
# by _resolve_api_key() below. Deliberately kept out of ResearchState: that state
# gets captured by LangSmith tracing, and a raw API key has no business ending up
# there.
_api_key_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "research_assistant_api_key", default=None
)

# Used only when nothing set the contextvar above (e.g. running the graph
# directly, outside AgentService/the server).
_FALLBACK_ENV_VAR = {
    ModelFamily.anthropic: "API_KEY",
    ModelFamily.openai: "OPENAI_API_KEY",
    ModelFamily.google: "GOOGLE_API_KEY",
}


def set_api_key(api_key: str | None) -> contextvars.Token:
    return _api_key_var.set(api_key)


def reset_api_key(token: contextvars.Token) -> None:
    _api_key_var.reset(token)


def _resolve_api_key(model_family: ModelFamily) -> str | None:
    return _api_key_var.get() or os.getenv(_FALLBACK_ENV_VAR[model_family])


@lru_cache(maxsize=32)
def _build_client(model_family: ModelFamily, model_name: str, api_key: str | None):
    if model_family == ModelFamily.anthropic:
        from langchain_anthropic import ChatAnthropic

        # temperature is omitted: the API only allows the default (1) while thinking is enabled.
        client = ChatAnthropic(model=model_name, api_key=api_key)
    elif model_family == ModelFamily.openai:
        from langchain_openai import ChatOpenAI

        client = ChatOpenAI(model=model_name, api_key=api_key)
    elif model_family == ModelFamily.google:
        from langchain_google_genai import ChatGoogleGenerativeAI

        client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    else:
        raise ValueError(f"Unsupported model family: {model_family}")

    return client


class _ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@lru_cache(maxsize=32)
def _build_tool_loop(
    model_family: ModelFamily, model_name: str, api_key: str | None, web_search: bool
):
    # The agentic tool-call loop itself, expressed as a graph instead of a hand-written
    # `while response.tool_calls:` - `tools_condition` routes to `tools` whenever the
    # latest AIMessage requests a tool call and to END otherwise, and `ToolNode` does the
    # dispatch/execution. ToolNode only turns *invalid tool arguments* into an error
    # message by default - any other exception a tool raises propagates and kills the
    # run, so tools must catch their own runtime failures (see search_in_web).
    loop_tools = _tools(web_search)
    client = _build_client(model_family, model_name, api_key).bind_tools(loop_tools)

    def call_model(state: _ToolLoopState):
        return {"messages": [client.invoke(state["messages"])]}

    builder = StateGraph(_ToolLoopState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(loop_tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()


@lru_cache(maxsize=32)
def _build_structured_client(
    model_family: ModelFamily, model_name: str, api_key: str | None, schema: type[BaseModel]
):
    return _build_client(model_family, model_name, api_key).with_structured_output(schema)


def ask(
    messages: list[BaseMessage],
    model_family: ModelFamily = DEFAULT_MODEL_FAMILY,
    model_name: str = DEFAULT_MODEL_NAME,
    use_tools: bool = False,
    web_search: bool = False,
) -> list[BaseMessage]:
    # `messages` must end with a HumanMessage. Returns only what this call produced -
    # any tool-call/tool-result round trip followed by the final AIMessage - never the
    # input, so callers can merge just the delta into their own persisted history.
    #
    # Tools are opt-in: every tool round resends the whole conversation, and a model
    # that can search will happily do so from nodes that don't need it (planning,
    # critique, rating), which burns tokens and search quota. `web_search` only matters
    # with use_tools: it adds search_in_web on top of the always-available date tool.
    api_key = _resolve_api_key(model_family)

    if not use_tools:
        return [_build_client(model_family, model_name, api_key).invoke(messages)]

    tool_loop = _build_tool_loop(model_family, model_name, api_key, web_search)
    result = tool_loop.invoke({"messages": messages})
    return result["messages"][len(messages):]


def ask_structured(
    messages: list[BaseMessage],
    schema: type[BaseModel],
    model_family: ModelFamily = DEFAULT_MODEL_FAMILY,
    model_name: str = DEFAULT_MODEL_NAME,
) -> BaseModel:
    client = _build_structured_client(
        model_family, model_name, _resolve_api_key(model_family), schema
    )
    return client.invoke(messages)
