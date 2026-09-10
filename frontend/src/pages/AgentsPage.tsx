import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import { useAgents, useDeleteAgent } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { EmptyState } from "../components/EmptyState";
import { useConfirm } from "../components/ConfirmDialogProvider";

export function AgentsPage() {
  const agents = useAgents();
  const deleteAgent = useDeleteAgent();
  const confirm = useConfirm();

  async function handleDelete(agentId: string, agentName: string) {
    const ok = await confirm({
      title: `Delete "${agentName}"?`,
      description: "This removes the agent and its configuration. This cannot be undone.",
      confirmText: "Delete",
      danger: true,
    });
    if (ok) deleteAgent.mutate(agentId);
  }

  return (
    <Box>
      <PageHeader
        title="Agents"
        description="Configure the models and behavior each research agent uses."
        action={
          <Button component={RouterLink} to="/agents/new" variant="contained" startIcon={<AddRoundedIcon />}>
            New agent
          </Button>
        }
      />

      {agents.isLoading && (
        <Stack sx={{ alignItems: "center", py: 8 }}>
          <CircularProgress />
        </Stack>
      )}
      {agents.isError && <Alert severity="error">Failed to load agents.</Alert>}
      {deleteAgent.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {deleteAgent.error instanceof ApiError ? deleteAgent.error.detail : "Failed to delete agent"}
        </Alert>
      )}

      {agents.isSuccess && agents.data.length === 0 && (
        <EmptyState
          icon={<SmartToyOutlinedIcon />}
          title="No agents yet"
          description="Create an agent and give it a model and behavior to start researching."
          action={
            <Button component={RouterLink} to="/agents/new" variant="contained" startIcon={<AddRoundedIcon />}>
              Create your first agent
            </Button>
          }
        />
      )}

      {agents.isSuccess && agents.data.length > 0 && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" },
            gap: 2,
          }}
        >
          {agents.data.map((agent) => (
            <Card key={agent.id} variant="outlined">
              <CardContent>
                <Stack direction="row" spacing={1.5} sx={{ mb: 1.5, alignItems: "center" }}>
                  <Avatar sx={{ bgcolor: "primary.main", width: 40, height: 40 }}>
                    <SmartToyOutlinedIcon fontSize="small" />
                  </Avatar>
                  <Typography variant="subtitle1" sx={{ overflowWrap: "anywhere" }}>
                    {agent.name}
                  </Typography>
                </Stack>
                {agent.has_config ? (
                  <Chip label="Configured" color="success" size="small" variant="outlined" />
                ) : (
                  <Chip label="Needs setup" color="warning" size="small" variant="outlined" />
                )}
              </CardContent>
              <CardActions sx={{ px: 2, pb: 2, pt: 0, justifyContent: "space-between" }}>
                {agent.has_config ? (
                  <Button
                    size="small"
                    component={RouterLink}
                    to={`/agents/${agent.id}/edit`}
                    state={{ agentName: agent.name }}
                    startIcon={<SettingsOutlinedIcon fontSize="small" />}
                  >
                    Configure
                  </Button>
                ) : (
                  <Button
                    size="small"
                    color="warning"
                    component={RouterLink}
                    to={`/agents/${agent.id}/config`}
                    state={{ agentName: agent.name }}
                    startIcon={<SettingsOutlinedIcon fontSize="small" />}
                  >
                    Set up now
                  </Button>
                )}
                <Tooltip title="Delete agent">
                  <IconButton
                    size="small"
                    color="error"
                    disabled={deleteAgent.isPending}
                    onClick={() => handleDelete(agent.id, agent.name)}
                  >
                    <DeleteOutlineRoundedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}
