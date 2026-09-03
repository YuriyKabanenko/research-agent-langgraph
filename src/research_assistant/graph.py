from langgraph.graph import StateGraph, START, END
from research_assistant.state import ResearchState
from research_assistant.nodes import *

agent_builder = StateGraph(ResearchState)

# Graph Nodes
agent_builder.add_node("validate_input", validate_input)
agent_builder.add_node("initial_plan", research_plan)
agent_builder.add_node("llm_research", llm_research)
agent_builder.add_node("critical_analysis", critical_analysis)
agent_builder.add_node("give_final_respond", give_final_respond)
agent_builder.add_node("error_print", error_print)

# Graph Edges
agent_builder.add_edge(START, "validate_input")
agent_builder.add_conditional_edges("validate_input", route_after_validate)
agent_builder.add_edge("validate_input", "initial_plan")
agent_builder.add_edge("initial_plan", "llm_research")
agent_builder.add_edge("llm_research", "critical_analysis")
agent_builder.add_conditional_edges("critical_analysis", route_after_analysis)

agent_builder.add_edge("error_print", END)
agent_builder.add_edge("give_final_respond", END)

# Compile the graph into an agent
agent = agent_builder.compile()


def main():
    initial_state = {
        "topic": "What is the sum of 125 and 225?",
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