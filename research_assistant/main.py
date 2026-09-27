from dotenv import load_dotenv

load_dotenv()

from research_assistant.state import ResearchMode
from langgraph.checkpoint.memory import InMemorySaver
from research_assistant.graph import CHECKPOINT_SERDE, build_agent, run_with_cli_review
import sys

def main():
    # Capture all arguments after the script name
    args = sys.argv[1:] 
    
    initial_state = {
        "topic": args[0],
        "research_mode": ResearchMode.quick,
        "research_plan": "",
        "messages": [],
        "research_steps": [],
        "critical_analysis": "",
        "retry_max_count": 3,
        "critique_threshold": 6,
        "should_split_topic": False,
        "subtopics": [],
        "subtopic_results": [],
        "human_feedback": "",
        "error_message": "",
        "final_response": "",
    }
    
    result = run_with_cli_review(build_agent(InMemorySaver(serde=CHECKPOINT_SERDE)), initial_state)
    
    if result.get("error_message"):
        print("Error:", result["error_message"])
        return
    elif result.get("final_response") is None:
        print("Error: No final response generated.")
        return
    else:
        print(result["final_response"]["content"])

if __name__ == "__main__":
    main()
