import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage, BaseMessage
from . import tools

MODEL_NAME = "claude-haiku-4-5"
api_key = os.getenv("API_KEY")

# Reads the ANTHROPIC_API_KEY environment variable automatically.
# temperature is omitted: the API only allows the default (1) while thinking is enabled.
client = ChatAnthropic(
    model=MODEL_NAME,
    api_key=api_key,
)

client = client.bind_tools([tools.get_current_date, tools.search_in_web])


def ask(messages: list[BaseMessage]) -> list[BaseMessage]:
    # `messages` must end with a HumanMessage. Returns only what this call produced -
    # any tool-call/tool-result round trip followed by the final AIMessage - never the
    # input, so callers can merge just the delta into their own persisted history.
    context = list(messages)
    new_messages = []
    response = client.invoke(context)

    while response.tool_calls:
        context.append(response)
        new_messages.append(response)
        for t in response.tool_calls:
            tool_func = tools.NAME_TO_TOOL.get(t["name"])
            tool_response = tool_func.invoke(t["args"])
            tool_message = ToolMessage(tool_response, tool_call_id=t["id"])
            context.append(tool_message)
            new_messages.append(tool_message)

        response = client.invoke(context)

    new_messages.append(response)
    return new_messages
