import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAgents } from "../hooks/useAgents";
import { useCreateResearch } from "../hooks/useResearch";
import { ApiError } from "../api/client";

export function NewResearchPage() {
  const agents = useAgents();
  const createResearch = useCreateResearch();
  const navigate = useNavigate();

  const [agentId, setAgentId] = useState("");
  const [topic, setTopic] = useState("");

  if (agents.isLoading) {
    return (
      <Container maxWidth="xs" sx={{ mt: 8 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (agents.isError) {
    return (
      <Container maxWidth="xs" sx={{ mt: 8 }}>
        <Alert severity="error">Failed to load agents.</Alert>
      </Container>
    );
  }

  const configuredAgents = (agents.data ?? []).filter((agent) => agent.has_config);

  if (configuredAgents.length === 0) {
    return (
      <Container maxWidth="xs" sx={{ mt: 8 }}>
        <Stack spacing={2}>
          <Typography>You need a configured agent before you can start research.</Typography>
          <Link component={RouterLink} to="/agents/new">
            Create an agent
          </Link>
        </Stack>
      </Container>
    );
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createResearch.mutate(
      { topic, agent_id: agentId },
      { onSuccess: () => navigate("/research") },
    );
  }

  return (
    <Container maxWidth="xs">
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 8 }}>
        <Stack spacing={2}>
          <Typography variant="h5">New research</Typography>
          {createResearch.isError && (
            <Alert severity="error">
              {createResearch.error instanceof ApiError
                ? createResearch.error.detail
                : "Failed to start research"}
            </Alert>
          )}
          <FormControl required>
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
            slotProps={{ htmlInput: { minLength: 5 } }}
          />
          <Button type="submit" variant="contained" disabled={createResearch.isPending || !agentId}>
            Start research
          </Button>
        </Stack>
      </Box>
    </Container>
  );
}
