import { useState, type FormEvent } from "react";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import TuneRoundedIcon from "@mui/icons-material/TuneRounded";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import VisibilityOffRoundedIcon from "@mui/icons-material/VisibilityOffRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
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
import { FormCard } from "./FormCard";

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
  const [showToken, setShowToken] = useState(false);
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
      <FormCard icon={<CheckCircleRoundedIcon />} title="You're all set">
        <Stack spacing={2}>
          <Alert severity="success" variant="outlined">
            Agent "{agentName}" is configured and ready to research.
          </Alert>
          <Button component={RouterLink} to="/agents" variant="contained">
            Back to agents
          </Button>
        </Stack>
      </FormCard>
    );
  }

  return (
    <FormCard
      icon={<TuneRoundedIcon />}
      title={`Configure "${agentName}"`}
      description="Choose a model and tune how hard the agent tries before it settles."
    >
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Stack spacing={2.5}>
          {createAgentConfig.isError && (
            <Alert severity="error">
              {createAgentConfig.error instanceof ApiError
                ? createAgentConfig.error.detail
                : "Failed to create config"}
            </Alert>
          )}
          <FormControl fullWidth>
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
          <FormControl fullWidth>
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
          <FormControl fullWidth>
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

          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
              Retry max count: {retryMaxCount}
            </Typography>
            <Slider
              value={retryMaxCount}
              onChange={(_, v) => setRetryMaxCount(v as number)}
              min={1}
              max={10}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              How many research/critique loops before it gives up and returns its best draft.
            </Typography>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
              Critique threshold: {critiqueThreshold}/10
            </Typography>
            <Slider
              value={critiqueThreshold}
              onChange={(_, v) => setCritiqueThreshold(v as number)}
              min={0}
              max={10}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              The self-critique score a draft needs to clear before the loop stops.
            </Typography>
          </Box>

          <TextField
            label="API token"
            type={showToken ? "text" : "password"}
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            required
            helperText="Encrypted at rest — never shown again after this."
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <VpnKeyOutlinedIcon fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowToken((v) => !v)}
                      edge="end"
                      size="small"
                      aria-label={showToken ? "Hide token" : "Show token"}
                    >
                      {showToken ? (
                        <VisibilityOffRoundedIcon fontSize="small" />
                      ) : (
                        <VisibilityRoundedIcon fontSize="small" />
                      )}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />
          <Button type="submit" variant="contained" size="large" disabled={createAgentConfig.isPending}>
            {createAgentConfig.isPending ? "Saving…" : "Save config"}
          </Button>
        </Stack>
      </Box>
    </FormCard>
  );
}
