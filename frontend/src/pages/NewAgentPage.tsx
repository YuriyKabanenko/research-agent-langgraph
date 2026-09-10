import { useState, type FormEvent } from "react";
import { Alert, Box, Button, Stack, TextField } from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import { useCreateAgent } from "../hooks/useAgents";
import { ApiError } from "../api/client";
import { AgentConfigForm } from "../components/AgentConfigForm";
import { FormCard } from "../components/FormCard";

export function NewAgentPage() {
  const [name, setName] = useState("");
  const createAgent = useCreateAgent();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createAgent.mutate({ name });
  }

  if (createAgent.isSuccess) {
    return <AgentConfigForm agentId={createAgent.data.id} agentName={createAgent.data.name} />;
  }

  return (
    <FormCard icon={<AddRoundedIcon />} title="New agent" description="Give it a name — you'll set its model next.">
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Stack spacing={2.5}>
          {createAgent.isError && (
            <Alert severity="error">
              {createAgent.error instanceof ApiError ? createAgent.error.detail : "Failed to create agent"}
            </Alert>
          )}
          <TextField
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoFocus
          />
          <Button type="submit" variant="contained" size="large" disabled={createAgent.isPending}>
            {createAgent.isPending ? "Creating…" : "Create agent"}
          </Button>
        </Stack>
      </Box>
    </FormCard>
  );
}
