from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Command
from research_assistant.state import ResearchState, ModelFamily, ResearchLoopState, SubtopicState
from research_assistant.nodes import *
from research_assistant.llm import model as llm_model

agent_builder = StateGraph(ResearchState)
research_loop_builder = StateGraph(ResearchLoopState)
subtopic_worker_builder = StateGraph(SubtopicState)

# Subgraph Research Loop Nodes
research_loop_builder.add_node("llm_research", llm_research)
research_loop_builder.add_node("critical_analysis", critical_analysis)

# Subgraph Research Loop Edges
research_loop_builder.add_edge(START, "llm_research")
research_loop_builder.add_edge("llm_research", "critical_analysis")
research_loop_builder.add_conditional_edges("critical_analysis", route_after_analysis)

# Compile Subgraph Research Loop
research_loop = research_loop_builder.compile()

# Subgraph Subtopic Worker - plans and researches a single subtopic (one per parallel
# Send from route_to_subtopics below), reusing the same research/critique loop as the
# single-topic path, then reduces its research_steps down to one SubtopicResult.
subtopic_worker_builder.add_node("research_plan", research_plan)
subtopic_worker_builder.add_node("research_loop", research_loop)
subtopic_worker_builder.add_node("pick_subtopic_result", pick_subtopic_result)

# Subgraph Subtopic Worker Edges
subtopic_worker_builder.add_edge(START, "research_plan")
subtopic_worker_builder.add_edge("research_plan", "research_loop")
subtopic_worker_builder.add_edge("research_loop", "pick_subtopic_result")
subtopic_worker_builder.add_edge("pick_subtopic_result", END)

# Compile Subgraph Subtopic Worker
subtopic_worker = subtopic_worker_builder.compile()

def _run_subtopic_worker(state: SubtopicState) -> dict:
    result = subtopic_worker.invoke(state)
    return {"subtopic_results": result["subtopic_results"]}

# Wraps research_loop instead of adding the compiled subgraph as a node directly: a
# subgraph node hands back its *whole* research_steps list, and the parent's
# operator.add reducer would append it to the steps the parent already has. Harmless
# on the first pass (parent starts at []), but human_review can send the graph back
# into the loop, which would duplicate every earlier step. Only new steps go back.
def _run_research_loop(state: ResearchState) -> dict:
    result = research_loop.invoke(state)
    return {
        "research_steps": result["research_steps"][len(state["research_steps"]):],
        # add_messages dedupes by message id, so the full list is safe to return.
        "messages": result["messages"],
        "critical_analysis": result["critical_analysis"],
    }

# Graph Nodes
agent_builder.add_node("validate_input", validate_input)
agent_builder.add_node("assess_topic_complexity", assess_topic_complexity)
agent_builder.add_node("split_topic", split_topic)
agent_builder.add_node("initial_plan", research_plan)
agent_builder.add_node("human_review", human_review)
agent_builder.add_node("give_final_respond", give_final_respond)
agent_builder.add_node("error_print", error_print)
agent_builder.add_node("research_loop", _run_research_loop)
agent_builder.add_node("subtopic_worker", _run_subtopic_worker)
agent_builder.add_node("combine_subtopics", combine_subtopics)

# Graph Edges
agent_builder.add_edge(START, "validate_input")
agent_builder.add_conditional_edges("validate_input", route_after_validate)
agent_builder.add_conditional_edges("assess_topic_complexity", route_after_complexity)
agent_builder.add_conditional_edges("split_topic", route_to_subtopics, ["subtopic_worker"])
agent_builder.add_edge("initial_plan", "research_loop")
agent_builder.add_edge("research_loop", "human_review")
# human_review routes itself via Command(goto=...) - no outgoing edges here.
agent_builder.add_edge("subtopic_worker", "combine_subtopics")
agent_builder.add_edge("combine_subtopics", END)
agent_builder.add_edge("error_print", END)
agent_builder.add_edge("give_final_respond", END)

# Serializer for every checkpointer this graph runs with. State holds our own enums,
# which LangGraph only deserializes with a warning (and will block in a future
# version) unless they're allow-listed explicitly.
CHECKPOINT_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("research_assistant.state", "ModelFamily"),
        ("research_assistant.state", "ResearchMode"),
    ]
)


# Compiled per caller rather than once at import time: interrupt() in human_review
# needs a checkpointer, and which one depends on the caller (Postgres in the server,
# in-memory for the CLI, none just to draw the graph). The subgraphs above inherit it.
def build_agent(checkpointer: BaseCheckpointSaver | None = None):
    return agent_builder.compile(checkpointer=checkpointer)


# Runs the agent from the terminal, asking for review on stdin each time human_review
# pauses the graph, until it completes.
def run_with_cli_review(agent, initial_state: dict, thread_id: str = "cli") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(initial_state, config)

    while "__interrupt__" in result:
        candidate = result["__interrupt__"][0].value["candidate"]
        print("=" * 60)
        print(f"DRAFT FOR REVIEW (rated {candidate['research_rate']}/10)")
        print("=" * 60)
        print(candidate["content"])
        print("=" * 60)

        feedback = input("Press Enter to approve, or type feedback to send it back: ").strip()
        decision = {"approved": True} if not feedback else {"approved": False, "feedback": feedback}
        result = agent.invoke(Command(resume=decision), config)

    return result


def main():
    initial_state = {
        "topic": "What is the sum of 125 and 225?",
        "model_family": ModelFamily.anthropic,
        "model_name": llm_model.DEFAULT_MODEL_NAME,
        "research_steps": [],
        "human_feedback": "",
        "error_message": "",
        "retry_max_count": 3,
        "critique_threshold": 6,
    }
    result = run_with_cli_review(build_agent(InMemorySaver(serde=CHECKPOINT_SERDE)), initial_state)

    if result.get("error_message"):
        print("Error:", result["error_message"])
        return


if __name__ == "__main__":
    main()
