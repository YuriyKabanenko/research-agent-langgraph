import re
from langchain_core.messages import SystemMessage, HumanMessage
from research_assistant.state import ResearchState, ResearchStep
from typing import Literal
import research_assistant.llm.model as model
from research_assistant.prompts import (
    research_system_promp,
    RESEARCH_USER_PROMPT,
    CRITIQUE_SYSTEM_PROMPT,
    EXTRACT_RESEARCH_CONTENT_PROMPT,
    RATE_RESEARCH_SYSTEM_PROMPT,
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
    return int(re.search(r"\d+", fallback_text).group())


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
    return int(re.search(r"\d+", fallback_text).group())


def _tools_used(new_messages: list) -> list[str]:
    return [t["name"] for m in new_messages for t in getattr(m, "tool_calls", [])]


# Conditional edge func. Check if the input is valid and then proceed to the next node.
def validate_input(state: ResearchState):
    topic = state["topic"]
    topic = topic.strip()

    if len(topic) == 0 or len(topic) > 100:
        return {"error_message": "Invalid topic length. Please provide a topic between 1 and 100 characters."}

    return {"topic": topic}

def route_after_validate(state: ResearchState) -> Literal["error_print", "initial_plan"]:
    if len(state["error_message"]) > 0:
        return "error_print"
    else:
        return "initial_plan"

def research_plan(state: ResearchState):
    system = _system_message("You are a research assistant. Please provide a research plan for the topic: " + state["topic"])
    human = HumanMessage("Topic is: " + state["topic"] + "\n Provide only a research plan with steps to follow.")
    
    response = model.ask(
        [system, human], model_family=state["model_family"], model_name=state["model_name"]
    )

    plan = response[-1].content.strip()

    return {"research_plan": plan}

# Research node. Core of researching process.
def llm_research(state: ResearchState):
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
def critical_analysis(state: ResearchState):
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
def route_after_analysis(state: ResearchState) -> Literal["llm_research", "give_final_respond"]:
    if state["critical_analysis"] == "" or len(state["research_steps"]) >= state["retry_max_count"] :
        return "give_final_respond"
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
