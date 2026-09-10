import { useLocation, useParams } from "react-router-dom";
import { AgentConfigForm } from "../components/AgentConfigForm";

interface ConfigureAgentLocationState {
  agentName?: string;
}

// Reached from the Agents list (AC-12), for an agent that was created but never
// configured. agentName travels via router state from AgentsPage's link so this
// doesn't need its own single-agent fetch (no GET /agents/{id} endpoint exists).
export function ConfigureAgentPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const location = useLocation();
  const state = location.state as ConfigureAgentLocationState | null;

  if (!agentId) {
    return null;
  }

  return <AgentConfigForm agentId={agentId} agentName={state?.agentName ?? agentId} />;
}
