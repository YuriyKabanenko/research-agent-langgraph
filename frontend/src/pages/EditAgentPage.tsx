import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
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
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import VisibilityOffRoundedIcon from "@mui/icons-material/VisibilityOffRounded";
import { useAgentConfig, useUpdateAgent, useUpdateAgentConfig } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import type { ResearchMode } from "../api/types";
import { FormCard } from "../components/FormCard";

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
  const [showToken, setShowToken] = useState(false);

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
    <FormCard icon={<SettingsOutlinedIcon />} title="Edit agent" description="Update its name or tune its behavior.">
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Stack spacing={2.5}>
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

          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />

          <FormControl fullWidth disabled={config.isLoading}>
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
              disabled={config.isLoading}
            />
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
              disabled={config.isLoading}
            />
          </Box>

          <TextField
            label="API token"
            type={showToken ? "text" : "password"}
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            placeholder="Leave blank to keep current token"
            helperText="Only fill this in to replace the stored token."
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

          <Button type="submit" variant="contained" size="large" disabled={isSaving || config.isLoading}>
            {isSaving ? "Saving…" : "Save changes"}
          </Button>
        </Stack>
      </Box>
    </FormCard>
  );
}
