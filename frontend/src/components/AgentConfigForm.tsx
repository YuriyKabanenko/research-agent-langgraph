import { useState, type FormEvent } from "react";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCreateAgentConfig } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import type { ModelFamily, ResearchMode } from "../api/types";
import {
  DEFAULT_MODEL_FAMILY,
  DEFAULT_MODEL_NAME,
  MODEL_FAMILIES,
  MODEL_FAMILY_LABELS,
  MODELS_BY_FAMILY,
} from "../constants/models";

interface AgentConfigFormProps {
  agentId: string;
  agentName: string;
}

// The config half of agent setup (AC-8/AC-9/AC-10). Used both inline on NewAgentPage
// right after creating an agent, and standalone on /agents/:agentId/config when an
// already-existing agent still needs configuring (AC-12).
export function AgentConfigForm({ agentId, agentName }: AgentConfigFormProps) {
  const [researchMode, setResearchMode] = useState<ResearchMode>("quick");
  const [retryMaxCount, setRetryMaxCount] = useState(3);
  const [critiqueThreshold, setCritiqueThreshold] = useState(6);
  const [apiToken, setApiToken] = useState("");
  const [modelFamily, setModelFamily] = useState<ModelFamily>(DEFAULT_MODEL_FAMILY);
  const [modelName, setModelName] = useState(DEFAULT_MODEL_NAME);
  const createAgentConfig = useCreateAgentConfig();

  function handleModelFamilyChange(family: ModelFamily) {
    setModelFamily(family);
    // Each family has its own set of model names - jump to that family's first
    // option so we never submit a model_name that doesn't belong to it.
    setModelName(MODELS_BY_FAMILY[family][0]);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createAgentConfig.mutate({
      agentId,
      body: {
        research_mode: researchMode,
        retry_max_count: retryMaxCount,
        critique_threshold: critiqueThreshold,
        api_token: apiToken,
        model_family: modelFamily,
        model_name: modelName,
      },
    });
  }

  if (createAgentConfig.isSuccess) {
    return (
      <Stack spacing={2}>
        <Alert severity="success">Agent "{agentName}" is configured.</Alert>
        <Link component={RouterLink} to="/agents">
          Back to agents
        </Link>
      </Stack>
    );
  }

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <Typography variant="h6">Configure "{agentName}"</Typography>
        {createAgentConfig.isError && (
          <Alert severity="error">
            {createAgentConfig.error instanceof ApiError
              ? createAgentConfig.error.detail
              : "Failed to create config"}
          </Alert>
        )}
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
        <FormControl>
          <InputLabel id="model-family-label">Model provider</InputLabel>
          <Select
            labelId="model-family-label"
            label="Model provider"
            value={modelFamily}
            onChange={(e) => handleModelFamilyChange(e.target.value as ModelFamily)}
          >
            {MODEL_FAMILIES.map((family) => (
              <MenuItem key={family} value={family}>
                {MODEL_FAMILY_LABELS[family]}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl>
          <InputLabel id="model-name-label">Model</InputLabel>
          <Select
            labelId="model-name-label"
            label="Model"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
          >
            {MODELS_BY_FAMILY[modelFamily].map((name) => (
              <MenuItem key={name} value={name}>
                {name}
              </MenuItem>
            ))}
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
          required
        />
        <Button type="submit" variant="contained" disabled={createAgentConfig.isPending}>
          Save config
        </Button>
      </Stack>
    </Box>
  );
}
