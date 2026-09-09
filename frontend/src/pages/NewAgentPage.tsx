import { useState, type FormEvent } from "react";
import { Alert, Box, Button, Container, Stack, TextField, Typography } from "@mui/material";
import { useCreateAgent } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import { AgentConfigForm } from "../components/AgentConfigForm";

export function NewAgentPage() {
  const [name, setName] = useState("");
  const createAgent = useCreateAgent();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createAgent.mutate({ name });
  }

  return (
    <Container maxWidth="xs">
      <Stack spacing={4} sx={{ mt: 8 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <Typography variant="h5">New agent</Typography>
            {createAgent.isError && (
              <Alert severity="error">
                {createAgent.error instanceof ApiError
                  ? createAgent.error.detail
                  : "Failed to create agent"}
              </Alert>
            )}
            <TextField
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={createAgent.isSuccess}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={createAgent.isPending || createAgent.isSuccess}
            >
              Create agent
            </Button>
          </Stack>
        </Box>

        {createAgent.isSuccess && (
          <AgentConfigForm agentId={createAgent.data.id} agentName={createAgent.data.name} />
        )}
      </Stack>
    </Container>
  );
}
