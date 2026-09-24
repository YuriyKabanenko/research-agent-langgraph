from typing_extensions import TypedDict, Annotated
from enum import Enum
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ResearchMode(Enum):
    quick = "quick"
    thorough = "thorough"

class ModelFamily(Enum):
    anthropic = "anthropic"
    openai = "openai"
    google = "google"

class ResearchStep(TypedDict):
    content: str
    tools_used: list[str]
    research_rate: int


class SubtopicResult(TypedDict):
    topic: str
    content: str
    tools_used: list[str]
    research_rate: int


class _SharedResearchFields(TypedDict):
    topic: Annotated[str, "The research topic being investigated."]
    model_family: Annotated[ModelFamily, "Which LLM provider family to run research on."] = ModelFamily.anthropic
    model_name: Annotated[str, "The specific model name to use within model_family."] = ""
    research_plan: Annotated[str, "The research plan outlining the steps to be taken during the research process."] = ""
    research_steps: Annotated[list[ResearchStep], "The steps taken during the research process.", operator.add] = []
    messages: Annotated[list[BaseMessage], "Full LLM conversation history, including tool calls and tool results.", add_messages] = []
    critical_analysis: Annotated[str, "A critical analysis of the research steps taken, highlighting any gaps or areas for improvement."] = ""
    retry_max_count: Annotated[int, "The max number of times the research process can be retried."] = 3
    critique_threshold: Annotated[int, "Minimum critique rating (1-10) at which research is accepted as final."] = 6


class ResearchLoopState(_SharedResearchFields):
    pass


# Per-subtopic worker's own schema: the shared loop fields plus the reducer-backed list
# each parallel Send-spawned branch appends its one result into.
class SubtopicState(_SharedResearchFields):
    subtopic_results: Annotated[list[SubtopicResult], "Per-subtopic research results, merged across parallel subtopic branches.", operator.add] = []


class ResearchState(_SharedResearchFields):
    research_mode: Annotated[ResearchMode, "The mode of research being conducted (quick or thorough)."] = ResearchMode.quick
    should_split_topic: Annotated[bool, "Whether the topic was judged complex enough to split into subtopics."] = False
    subtopics: Annotated[list[str], "The subtopics the original topic was split into, when complex enough."] = []
    subtopic_results: Annotated[list[SubtopicResult], "Per-subtopic research results, merged across parallel subtopic branches.", operator.add] = []
    error_message: Annotated[str, "An error message describing any issues encountered during the research process."] = ""
    final_response: Annotated[ResearchStep, "The final response generated after completing the research process."] = ""