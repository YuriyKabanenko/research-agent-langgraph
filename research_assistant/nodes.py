import re
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import END
from langgraph.types import Send
from research_assistant.state import (
    ResearchState,
    ResearchLoopState,
    ResearchStep,
    SubtopicState,
    SubtopicResult,
)
from typing import Literal
import research_assistant.llm.model as model
from research_assistant.prompts import (
    research_system_promp,
    RESEARCH_USER_PROMPT,
    CRITIQUE_SYSTEM_PROMPT,
    EXTRACT_RESEARCH_CONTENT_PROMPT,
    RATE_RESEARCH_SYSTEM_PROMPT,
    ASSESS_TOPIC_COMPLEXITY_PROMPT,
    SPLIT_TOPIC_PROMPT,
)

SYSTEM_MESSAGE_ID = "system"

def _system_message(prompt: str) -> SystemMessage:
    # Anthropic accepts exactly one system prompt per call, always first in the list.
    # Every node has a different persona (init / research / critique), so giving each
    # SystemMessage this fixed id makes the add_messages reducer replace the previous
    # one in place in state["messages"] instead of accumulating several system
    # messages into shared history, which the API wouldn't accept anyway.
    return SystemMessage(prompt, id=SYSTEM_MESSAGE_ID)


RESEARCH_TAG_RE = re.compile(r"<research>(.*?)</research>", re.DOTALL)
RESEARCH_RATE_RE = re.compile(r"research_rate\s*=\s*(\d+)")
CRITIQUE_RATE_RE = re.compile(r"critique_rate\s*=\s*(\d+)")
SPLIT_TOPIC_RE = re.compile(r"split_topic\s*=\s*(yes|no)", re.IGNORECASE)


def _extract_research_content(response_text: str, model_family, model_name: str) -> str:
    match = RESEARCH_TAG_RE.search(response_text)
    if match:
        return match.group(1).strip()

    # Model didn't follow the <research> tag format - fall back to a focused,
    # context-free call whose only job is pulling the content out, rather than
    # guessing with more regex.
    fallback = model.ask(
        [SystemMessage(EXTRACT_RESEARCH_CONTENT_PROMPT), HumanMessage(response_text)],
        model_family=model_family,
        model_name=model_name,
    )
    return fallback[-1].content.strip()


def _extract_research_rate(
    response_text: str, topic: str, plan: str, content: str, model_family, model_name: str
) -> int:
    match = RESEARCH_RATE_RE.search(response_text)
    if match:
        return int(match.group(1))

    # Model didn't follow the research_rate=X format - rate the already-extracted
    # content in isolation (fresh context, no tool-call noise or commentary) so the
    # judgment reflects the notes themselves, not formatting quirks in the response.
    fallback = model.ask(
        [SystemMessage(RATE_RESEARCH_SYSTEM_PROMPT(topic, plan)), HumanMessage(content)],
        model_family=model_family,
        model_name=model_name,
    )
    fallback_text = fallback[-1].content.strip()
    return _first_int(fallback_text, default=5)


def _extract_critique_rate(
    response_text: str, topic: str, plan: str, content: str, model_family, model_name: str
) -> int:
    match = CRITIQUE_RATE_RE.search(response_text)
    if match:
        return int(match.group(1))

    # Model didn't follow the critique_rate=X format - fall back to rating the
    # content directly with the shared rating prompt.
    fallback = model.ask(
        [SystemMessage(RATE_RESEARCH_SYSTEM_PROMPT(topic, plan)), HumanMessage(content)],
        model_family=model_family,
        model_name=model_name,
    )
    fallback_text = fallback[-1].content.strip()
    return _first_int(fallback_text, default=5)


def _tools_used(new_messages: list) -> list[str]:
    return [t["name"] for m in new_messages for t in getattr(m, "tool_calls", [])]


def _first_int(text: str, default: int) -> int:
    # Even the fallback rating call can come back without a digit at all (e.g. the
    # model apologizes instead of complying) - fall back to a neutral mid-scale rating
    # rather than crashing the whole branch on `.group()` of a None match.
    match = re.search(r"\d+", text)
    return int(match.group()) if match else default


def _parse_subtopics(text: str) -> list[str]:
    subtopics = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
        if cleaned:
            subtopics.append(cleaned)
    return subtopics


# Conditional edge func. Check if the input is valid and then proceed to the next node.
def validate_input(state: ResearchState):
    topic = state["topic"]
    topic = topic.strip()

    if len(topic) == 0 or len(topic) > 100:
        return {"error_message": "Invalid topic length. Please provide a topic between 1 and 100 characters."}

    return {"topic": topic}

def route_after_validate(state: ResearchState) -> Literal["error_print", "assess_topic_complexity"]:
    if len(state["error_message"]) > 0:
        return "error_print"
    else:
        return "assess_topic_complexity"

# LLM call deciding whether the topic is complex enough to split into subtopics.
def assess_topic_complexity(state: ResearchState):
    system = _system_message(ASSESS_TOPIC_COMPLEXITY_PROMPT)
    human = HumanMessage("Topic: " + state["topic"])

    new_messages = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )
    verdict = new_messages[-1].content.strip()
    match = SPLIT_TOPIC_RE.search(verdict)
    should_split = bool(match) and match.group(1).lower() == "yes"

    return {
        "messages": [system, human, new_messages[-1]],
        "should_split_topic": should_split,
    }

def route_after_complexity(state: ResearchState) -> Literal["initial_plan", "split_topic"]:
    if state["should_split_topic"]:
        return "split_topic"
    else:
        return "initial_plan"

# LLM call breaking a complex topic down into narrower subtopics to research in parallel.
def split_topic(state: ResearchState):
    system = _system_message(SPLIT_TOPIC_PROMPT)
    human = HumanMessage("Topic: " + state["topic"])

    new_messages = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )
    subtopics = _parse_subtopics(new_messages[-1].content)
    if not subtopics:
        # Model didn't return anything parseable - fall back to a single "subtopic"
        # equal to the original topic so the fan-out below still has something to do.
        subtopics = [state["topic"]]

    return {
        "messages": [system, human, new_messages[-1]],
        "subtopics": subtopics,
    }

# Conditional edge func. Fans out one parallel `subtopic_worker` run per subtopic - each
# Send's payload is the *entire* input state for that branch (it isn't merged with the
# rest of the parent state), so it must include everything SubtopicState's nodes read.
def route_to_subtopics(state: ResearchState) -> list[Send]:
    return [
        Send(
            "subtopic_worker",
            {
                "topic": subtopic,
                "model_family": state["model_family"],
                "model_name": state["model_name"],
                "research_plan": "",
                "research_steps": [],
                "messages": [],
                "critical_analysis": "",
                "retry_max_count": state["retry_max_count"],
                "critique_threshold": state["critique_threshold"],
                "subtopic_results": [],
            },
        )
        for subtopic in state["subtopics"]
    ]

# Reduces one subtopic branch's research_steps down to its single best-rated result.
def pick_subtopic_result(state: SubtopicState):
    best = max(state["research_steps"], key=lambda step: step["research_rate"])
    result = SubtopicResult(
        topic=state["topic"],
        content=best["content"],
        tools_used=best["tools_used"],
        research_rate=best["research_rate"],
    )
    return {"subtopic_results": [result]}

# Fan-in node. By the time this runs, every parallel subtopic_worker branch has already
# appended its result into subtopic_results via that field's operator.add reducer - no
# manual "wait for all branches" logic needed here, just combine what's already there.
def combine_subtopics(state: ResearchState):
    results = state["subtopic_results"]
    sections = [
        f"## {r['topic']} (rated {r['research_rate']}/10)\n{r['content']}"
        for r in results
    ]
    combined_content = "\n\n".join(sections)
    tools_used = sorted({t for r in results for t in r["tools_used"]})
    avg_rate = round(sum(r["research_rate"] for r in results) / len(results))

    final = ResearchStep(content=combined_content, tools_used=tools_used, research_rate=avg_rate)

    print("=" * 60)
    print("FINAL RESEARCH RESULT (COMBINED FROM SUBTOPICS)")
    print("=" * 60)
    print(f"Subtopics: {len(results)}")
    print(f"Average rate: {avg_rate}/10")
    print("-" * 60)
    print(combined_content)
    print("=" * 60)

    return {"final_response": final}

def research_plan(state: ResearchState):
    system = _system_message("You are a research assistant. Please provide a research plan for the topic: " + state["topic"])
    human = HumanMessage("Topic is: " + state["topic"] + "\n Provide only a research plan with steps to follow.")
    
    response = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )

    plan = response[-1].content.strip()

    return {"research_plan": plan}

# Research node. Core of researching process.
def llm_research(state: ResearchLoopState):
    if state["critical_analysis"]:
        instruction = "Fix research accroding to this analysis: " + state["critical_analysis"]
    else:
        instruction = RESEARCH_USER_PROMPT

    rounds = [
        f"Round {i + 1} (rated {step['research_rate']}/10):\n{step['content']}"
        for i, step in enumerate(state["research_steps"])
    ]
    research_so_far = "\n\n".join(rounds)

    system = _system_message(research_system_promp(state["topic"]))
    human = HumanMessage(
        f"Topic: {state['topic']}\n\nResearch Plan: {state['research_plan']}\n\n"
        f"Research so far:\n{research_so_far}\n\nAdditional instructions: {instruction}"
    )

    new_messages = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )
    response_text = new_messages[-1].content
    content = _extract_research_content(response_text, state["model_family"], state["model_name"])
    rate = _extract_research_rate(
        response_text,
        state["topic"],
        state["research_plan"],
        content,
        state["model_family"],
        state["model_name"],
    )

    step = ResearchStep(content=content, tools_used=_tools_used(new_messages), research_rate=rate)

    return {
        "messages": [system, human, new_messages[-1]],
        "research_steps": [step],
    }

# Critical analysis node. Rates the latest research step and decides whether it clears the bar.
def critical_analysis(state: ResearchLoopState):
    system = _system_message(CRITIQUE_SYSTEM_PROMPT)
    human = HumanMessage( "Topic: " + state["topic"] + "\n" + state["research_steps"][-1]["content"])

    new_messages = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )
    verdict = new_messages[-1].content
    critique_rate = _extract_critique_rate(
        verdict,
        state["topic"],
        state["research_plan"],
        state["research_steps"][-1]["content"],
        state["model_family"],
        state["model_name"],
    )
    research_is_done = critique_rate >= state["critique_threshold"]

    return {
        "messages": [system, human, new_messages[-1]],
        "critical_analysis": "" if research_is_done else verdict,
    }

# Conditional edge func. Check if the research is done or not and then proceed to the next node.
def route_after_analysis(state: ResearchLoopState) -> Literal["llm_research", "__end__"]:
    if state["critical_analysis"] == "" or len(state["research_steps"]) >= state["retry_max_count"] :
        return END
    else:
        return "llm_research"


# Node for generating a final response based on researches
def give_final_respond(state: ResearchState):
    max_rated_response = max(state["research_steps"], key=lambda step: step["research_rate"])

    tools_used = ", ".join(max_rated_response["tools_used"]) if max_rated_response["tools_used"] else "none"
    print("=" * 60)
    print("FINAL RESEARCH RESULT")
    print("=" * 60)
    print(f"Research rate: {max_rated_response['research_rate']}/10")
    print(f"Tools used: {tools_used}")
    print("-" * 60)
    print(max_rated_response["content"])
    print("=" * 60)

    return {"final_response": max_rated_response}

def error_print(state: ResearchState):
    print("Error: " + state["error_message"])
