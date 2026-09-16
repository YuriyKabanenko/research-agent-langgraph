from langgraph.graph import StateGraph, START, END
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

# Graph Nodes
agent_builder.add_node("validate_input", validate_input)
agent_builder.add_node("assess_topic_complexity", assess_topic_complexity)
agent_builder.add_node("split_topic", split_topic)
agent_builder.add_node("initial_plan", research_plan)
agent_builder.add_node("give_final_respond", give_final_respond)
agent_builder.add_node("error_print", error_print)
agent_builder.add_node("research_loop", research_loop)
agent_builder.add_node("subtopic_worker", _run_subtopic_worker)
agent_builder.add_node("combine_subtopics", combine_subtopics)

# Graph Edges
agent_builder.add_edge(START, "validate_input")
agent_builder.add_conditional_edges("validate_input", route_after_validate)
agent_builder.add_conditional_edges("assess_topic_complexity", route_after_complexity)
agent_builder.add_conditional_edges("split_topic", route_to_subtopics, ["subtopic_worker"])
agent_builder.add_edge("initial_plan", "research_loop")
agent_builder.add_edge("research_loop", "give_final_respond")
agent_builder.add_edge("subtopic_worker", "combine_subtopics")
agent_builder.add_edge("combine_subtopics", END)
agent_builder.add_edge("error_print", END)
agent_builder.add_edge("give_final_respond", END)

# Compile the graph into an agent
agent = agent_builder.compile()


def main():
    initial_state = {
        "topic": "What is the sum of 125 and 225?",
        "model_family": ModelFamily.anthropic,
        "model_name": llm_model.DEFAULT_MODEL_NAME,
        "research_steps": [],
        "error_message": "",
        "retry_max_count": 3,
        "critique_threshold": 6,
    }
    result = agent.invoke(initial_state)

    if result.get("error_message"):
        print("Error:", result["error_message"])
        return


if __name__ == "__main__":
    main()