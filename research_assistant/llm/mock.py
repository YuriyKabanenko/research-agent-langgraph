"""Offline stand-ins for the LLM and web search, so the app can be exercised end to end
without spending API credits.

    MOCK_LLM=1            every provider is replaced by MockChatModel (no API key needed)
    MOCK_WEB_SEARCH=1     search_in_web returns canned results instead of calling Tavily
    MOCK_STREAM_DELAY=0.03  seconds between streamed chunks (default 0.03)

The mock sits at the chat-model level rather than replacing `ask()`, so everything above
it - bind_tools, the tool-call loop, ToolNode, with_structured_output, and token streaming
(stream_mode="messages" / astream_events) - runs the same code path as a real model.
"""
import json
import os
import re
import time
import uuid
from typing import Any, Iterator

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def llm_mocked() -> bool:
    return _flag("MOCK_LLM")


def web_search_mocked() -> bool:
    return _flag("MOCK_WEB_SEARCH")


def _stream_delay() -> float:
    try:
        return float(os.getenv("MOCK_STREAM_DELAY", "0.03"))
    except ValueError:
        return 0.03


# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------

def mock_search(query: str) -> str:
    # Same shape search_in_web builds from real Tavily results: title, URL, snippet.
    time.sleep(_stream_delay() * 10)
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-") or "query"
    return "\n\n".join(
        f"Mock result {i} for '{query}'\n"
        f"https://example.com/{slug}/{i}\n"
        f"Mock snippet {i}: a made-up fact about {query}, returned by MOCK_WEB_SEARCH."
        for i in range(1, 4)
    )


# ---------------------------------------------------------------------------
# Chat model
# ---------------------------------------------------------------------------

# llm_research's human message lists earlier rounds as "Round N (rated ...)"; the mock
# stamps its notes with the round number so the critique mock can read it back.
_ROUND_RE = re.compile(r"^Round \d+ \(rated", re.MULTILINE)
_NOTES_ROUND_RE = re.compile(r"\(mock round (\d+)\)")


def _last_human_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def _topic(text: str) -> str:
    match = re.search(r"Topic(?: is)?:\s*(.+)", text)
    return match.group(1).strip() if match else "the topic"


class MockChatModel(BaseChatModel):
    """Deterministic fake that answers every prompt this graph sends.

    Behaviour, chosen so every branch of the graph can be reached:
      - tools bound, no tool result yet -> calls search_in_web (or get_current_date)
      - tools bound, tool result present -> <research> notes + research_rate=X
      - TopicComplexity schema          -> should_split=True if the topic contains "complex"
      - CritiqueVerdict schema          -> rating 4 on round 1 (forces one retry), 8 after
      - SubtopicList schema             -> three subtopics
      - anything else                   -> short plain text
    """

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        # Only needs the tool names and schemas; convert the same way real providers do
        # so with_structured_output (which binds the schema as a tool) works too.
        return self.bind(tools=[convert_to_openai_tool(t) for t in tools], tool_choice=tool_choice, **kwargs)

    # -- response selection ------------------------------------------------

    def _respond(self, messages: list[BaseMessage], tools: list[dict]) -> AIMessage:
        tool_names = [t["function"]["name"] for t in tools]
        text = _last_human_text(messages)
        topic = _topic(text)

        schema = next((n for n in tool_names if n in _STRUCTURED), None)
        if schema:
            return self._tool_call(schema, _STRUCTURED[schema](text, topic))

        if tool_names:
            already_called = any(isinstance(m, ToolMessage) for m in messages)
            if not already_called:
                if "search_in_web" in tool_names:
                    return self._tool_call("search_in_web", {"query": topic})
                return self._tool_call(tool_names[0], {})
            return AIMessage(_research_notes(messages, text, topic))

        return AIMessage(
            f"Mock response about {topic}.\n1. Define the scope.\n2. Collect key facts.\n"
            "3. Summarize findings."
        )

    @staticmethod
    def _tool_call(name: str, args: dict) -> AIMessage:
        return AIMessage("", tool_calls=[{"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:12]}"}])

    # -- BaseChatModel hooks -----------------------------------------------

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        message = self._respond(messages, kwargs.get("tools") or [])
        delay = _stream_delay()

        if message.tool_calls:
            # Real providers stream tool calls as tool_call_chunks with JSON-string args.
            time.sleep(delay)
            call = message.tool_calls[0]
            yield ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[{
                        "name": call["name"], "args": json.dumps(call["args"]),
                        "id": call["id"], "index": 0,
                    }],
                )
            )
            return

        # Word-sized chunks, whitespace kept, so concatenation rebuilds the exact text.
        # No on_llm_new_token here: BaseChatModel already fires it for every yielded chunk.
        for piece in re.findall(r"\S+\s*|\s+", message.content):
            time.sleep(delay)
            yield ChatGenerationChunk(message=AIMessageChunk(content=piece))

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Non-streaming calls take about as long as streaming ones, so timing-dependent
        # UI (spinners, polling) behaves the same either way.
        time.sleep(_stream_delay() * 10)
        message = self._respond(messages, kwargs.get("tools") or [])
        return ChatResult(generations=[ChatGeneration(message=message)])


def _research_notes(messages: list[BaseMessage], text: str, topic: str) -> str:
    round_no = len(_ROUND_RE.findall(text)) + 1
    sources = next(
        (m.content for m in reversed(messages) if isinstance(m, ToolMessage)), ""
    )
    first_source = sources.splitlines()[0] if sources else "no sources"
    rate = min(5 + round_no, 10)
    return (
        f"<research>\nMock research notes on {topic} (mock round {round_no}).\n\n"
        f"- Key point A about {topic}.\n- Key point B about {topic}.\n"
        f"- Based on: {first_source}\n</research>\nresearch_rate={rate}"
    )


def _critique(text: str, topic: str) -> dict:
    match = _NOTES_ROUND_RE.search(text)
    round_no = int(match.group(1)) if match else 2
    if round_no <= 1:
        return {"feedback": "Mock critique: add concrete examples and sources.", "rating": 4}
    return {"feedback": "Mock critique: good enough.", "rating": 8}


_STRUCTURED = {
    "TopicComplexity": lambda text, topic: {
        "reason": "Mock decision based on whether the topic contains 'complex'.",
        "should_split": "complex" in topic.lower(),
    },
    "SubtopicList": lambda text, topic: {
        "subtopics": [f"{topic}: history", f"{topic}: current state", f"{topic}: future outlook"],
    },
    "CritiqueVerdict": _critique,
}
