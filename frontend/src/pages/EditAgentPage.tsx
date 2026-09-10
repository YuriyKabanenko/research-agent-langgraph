import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAgentConfig, useUpdateAgent, useUpdateAgentConfig } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import type { ResearchMode } from "../api/types";

interface EditAgentLocationState {
  agentName?: string;
}

// Reached from the Agents list for an already-configured agent. Name comes from router
// state (same convention as ConfigureAgentPage); config values are fetched fresh since
// the list only carries a has_config flag, not the actual settings.
export function EditAgentPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as EditAgentLocationState | null;

  const config = useAgentConfig(agentId);
  const updateAgent = useUpdateAgent();
  const updateAgentConfig = useUpdateAgentConfig();

  const [name, setName] = useState(state?.agentName ?? "");
  const [researchMode, setResearchMode] = useState<ResearchMode>("quick");
  const [retryMaxCount, setRetryMaxCount] = useState(3);
  const [critiqueThreshold, setCritiqueThreshold] = useState(6);
  const [apiToken, setApiToken] = useState("");

  useEffect(() => {
    if (config.data) {
      setResearchMode(config.data.research_mode);
      setRetryMaxCount(config.data.retry_max_count);
      setCritiqueThreshold(config.data.critique_threshold);
    }
  }, [config.data]);

  if (!agentId) {
    return null;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!agentId) return;

    await Promise.all([
      updateAgent.mutateAsync({ agentId, body: { name } }),
      updateAgentConfig.mutateAsync({
        agentId,
        body: {
          research_mode: researchMode,
          retry_max_count: retryMaxCount,
          critique_threshold: critiqueThreshold,
          ...(apiToken ? { api_token: apiToken } : {}),
        },
      }),
    ]);
    navigate("/agents");
  }

  const isSaving = updateAgent.isPending || updateAgentConfig.isPending;
  const saveError = updateAgent.error ?? updateAgentConfig.error;

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <Typography variant="h5">Edit agent</Typography>

          {config.isLoading && <CircularProgress size={24} />}
          {config.isError && (
            <Alert severity="error">
              {config.error instanceof ApiError ? config.error.detail : "Failed to load config"}
            </Alert>
          )}
          {saveError && (
            <Alert severity="error">
              {saveError instanceof ApiError ? saveError.detail : "Failed to save agent"}
            </Alert>
          )}

          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />

          <FormControl>
            <InputLabel id="research-mode-label">Research mode</InputLabel>
            <Select
              labelId="research-mode-label"
              label="Research mode"
              value={researchMode}
              onChange={(e) => setResearchMode(e.target.value as ResearchMode)}
            >
              <MenuItem value="quick">Quick</MenuItem>
              <MenuItem value="thorough">Thorough</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Retry max count"
            type="number"
            value={retryMaxCount}
            onChange={(e) => setRetryMaxCount(Number(e.target.value))}
            required
          />
          <TextField
            label="Critique threshold"
            type="number"
            value={critiqueThreshold}
            onChange={(e) => setCritiqueThreshold(Number(e.target.value))}
            required
          />
          <TextField
            label="API token"
            type="password"
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            placeholder="Leave blank to keep current token"
          />

          <Button type="submit" variant="contained" disabled={isSaving || config.isLoading}>
            Save changes
          </Button>
        </Stack>
      </Box>
    </Container>
  );
}
