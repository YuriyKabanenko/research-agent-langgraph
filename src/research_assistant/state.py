from typing_extensions import TypedDict, Annotated
from enum import Enum
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ResearchMode(Enum):
    quick = 1,
    thorough = 2,

class ResearchStep(TypedDict):
    content: str
    tools_used: list[str]
    research_rate: int


class ResearchState(TypedDict):
    topic: Annotated[str, "The research topic being investigated."]
    research_mode: Annotated[ResearchMode, "The mode of research being conducted (quick or thorough)."] = ResearchMode.quick
    research_plan: Annotated[str, "The research plan outlining the steps to be taken during the research process."] = ""
    research_steps: Annotated[list[ResearchStep], "The steps taken during the research process.", operator.add] = []
    messages: Annotated[list[BaseMessage], "Full LLM conversation history, including tool calls and tool results.", add_messages] = []
    critical_analysis: Annotated[str, "A critical analysis of the research steps taken, highlighting any gaps or areas for improvement."] = ""
    retry_max_count: Annotated[int, "The max number of times the research process can be retried."] = 3
    critique_threshold: Annotated[int, "Minimum critique rating (1-10) at which research is accepted as final."] = 6
    error_message: Annotated[str, "An error message describing any issues encountered during the research process."] = ""
    final_response: Annotated[ResearchStep, "The final response generated after completing the research process."] = ""