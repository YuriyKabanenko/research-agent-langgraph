import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { useAgents } from "../hooks/useAgents";
import { useCreateResearch } from "../hooks/useResearch";
import { ApiError } from "../api/client";
import { FormCard } from "../components/FormCard";

export function NewResearchPage() {
  const agents = useAgents();
  const createResearch = useCreateResearch();
  const navigate = useNavigate();

  const [agentId, setAgentId] = useState("");
  const [topic, setTopic] = useState("");

  if (agents.isLoading) {
    return (
      <FormCard icon={<TravelExploreOutlinedIcon />} title="New research">
        <Stack sx={{ alignItems: "center", py: 4 }}>
          <CircularProgress />
        </Stack>
      </FormCard>
    );
  }

  if (agents.isError) {
    return (
      <FormCard icon={<TravelExploreOutlinedIcon />} title="New research">
        <Alert severity="error">Failed to load agents.</Alert>
      </FormCard>
    );
  }

  const configuredAgents = (agents.data ?? []).filter((agent) => agent.has_config);

  if (configuredAgents.length === 0) {
    return (
      <FormCard icon={<TravelExploreOutlinedIcon />} title="New research">
        <Stack spacing={2}>
          <Typography color="text.secondary">
            You need a configured agent before you can start research.
          </Typography>
          <Button component={RouterLink} to="/agents/new" variant="contained">
            Create an agent
          </Button>
        </Stack>
      </FormCard>
    );
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createResearch.mutate({ topic, agent_id: agentId }, { onSuccess: () => navigate("/research") });
  }

  return (
    <FormCard
      icon={<TravelExploreOutlinedIcon />}
      title="New research"
      description="Pick an agent and give it a topic to dig into."
    >
      <Stack component="form" onSubmit={handleSubmit} spacing={2.5} noValidate>
        {createResearch.isError && (
          <Alert severity="error">
            {createResearch.error instanceof ApiError ? createResearch.error.detail : "Failed to start research"}
          </Alert>
        )}
        <FormControl required fullWidth>
          <InputLabel id="agent-label">Agent</InputLabel>
          <Select
            labelId="agent-label"
            label="Agent"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
          >
            {configuredAgents.map((agent) => (
              <MenuItem key={agent.id} value={agent.id}>
                {agent.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          label="Topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          required
          autoFocus
          multiline
          minRows={2}
          helperText="At least 5 characters — be as specific as you like."
          slotProps={{ htmlInput: { minLength: 5 } }}
        />
        <Button type="submit" variant="contained" size="large" disabled={createResearch.isPending || !agentId}>
          {createResearch.isPending ? "Starting…" : "Start research"}
        </Button>
      </Stack>
    </FormCard>
  );
}
