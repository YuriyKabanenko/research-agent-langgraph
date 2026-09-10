import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  Container,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useAgents, useDeleteAgent } from "../hooks/useAgents";
import { ApiError } from "../api/client";

export function AgentsPage() {
  const agents = useAgents();
  const deleteAgent = useDeleteAgent();

  function handleDelete(agentId: string, agentName: string) {
    if (!window.confirm(`Delete agent "${agentName}"? This cannot be undone.`)) {
      return;
    }
    deleteAgent.mutate(agentId);
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Agents
      </Typography>

      {agents.isLoading && <CircularProgress />}
      {agents.isError && <Alert severity="error">Failed to load agents.</Alert>}
      {deleteAgent.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {deleteAgent.error instanceof ApiError ? deleteAgent.error.detail : "Failed to delete agent"}
        </Alert>
      )}

      {agents.isSuccess && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {agents.data.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>
                    {agent.has_config ? (
                      <Chip label="Configured" color="success" size="small" />
                    ) : (
                      <Link
                        component={RouterLink}
                        to={`/agents/${agent.id}/config`}
                        state={{ agentName: agent.name }}
                      >
                        Not configured - set up now
                      </Link>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {agent.has_config && (
                      <Button
                        size="small"
                        component={RouterLink}
                        to={`/agents/${agent.id}/edit`}
                        state={{ agentName: agent.name }}
                      >
                        Edit
                      </Button>
                    )}
                    <Button
                      size="small"
                      color="error"
                      disabled={deleteAgent.isPending}
                      onClick={() => handleDelete(agent.id, agent.name)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {agents.data.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3}>
                    No agents yet. <RouterLink to="/agents/new">Create one</RouterLink>.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
}
