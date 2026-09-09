import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { ChipProps } from "@mui/material";
import { useDeleteResearch, useResearches } from "../hooks/useResearch";
import { ApiError } from "../api/client";
import type { ResearchResponse, ResearchStatus } from "../api/types";

const STATUS_COLOR: Record<ResearchStatus, ChipProps["color"]> = {
  pending: "default",
  running: "info",
  completed: "success",
  failed: "error",
};

function slugify(topic: string): string {
  return topic.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function downloadResearchMarkdown(run: ResearchResponse) {
  const lines = [
    `# ${run.topic}`,
    "",
    `- **Agent:** ${run.agent_name}`,
    `- **Rate:** ${run.research_rate != null ? `${run.research_rate}/10` : "n/a"}`,
    `- **Tools used:** ${run.tools_used && run.tools_used.length > 0 ? run.tools_used.join(", ") : "none"}`,
    `- **Created:** ${new Date(run.created_at).toLocaleString()}`,
    "",
    "---",
    "",
    run.research ?? "",
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const slug = slugify(run.topic) || "research";
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slug}-${run.id.slice(0, 8)}.md`;
  link.click();
  URL.revokeObjectURL(url);
}

export function ResearchesPage() {
  const research = useResearches();
  const deleteResearch = useDeleteResearch();

  function handleDelete(run: ResearchResponse) {
    if (!window.confirm(`Delete research "${run.topic}"? This cannot be undone.`)) {
      return;
    }
    deleteResearch.mutate(run.id);
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5">Research</Typography>
        <Button variant="outlined" onClick={() => research.refetch()} disabled={research.isFetching}>
          Refresh
        </Button>
      </Box>

      {research.isLoading && <CircularProgress />}
      {research.isError && <Alert severity="error">Failed to load research runs.</Alert>}
      {deleteResearch.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {deleteResearch.error instanceof ApiError
            ? deleteResearch.error.detail
            : "Failed to delete research"}
        </Alert>
      )}

      {research.isSuccess && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Topic</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Rate</TableCell>
                <TableCell>Tools used</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Result</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {research.data.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>{run.topic}</TableCell>
                  <TableCell>{run.agent_name}</TableCell>
                  <TableCell>
                    <Chip label={run.status} color={STATUS_COLOR[run.status]} size="small" />
                  </TableCell>
                  <TableCell>{run.research_rate != null ? `${run.research_rate}/10` : "—"}</TableCell>
                  <TableCell sx={{ maxWidth: 200 }}>
                    {run.tools_used && run.tools_used.length > 0 ? (
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {run.tools_used.map((tool) => (
                          <Chip key={tool} label={tool} size="small" variant="outlined" />
                        ))}
                      </Box>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                  <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                  <TableCell sx={{ maxWidth: 400, whiteSpace: "pre-wrap" }}>
                    {run.status === "completed" && (
                      <Button size="small" variant="outlined" onClick={() => downloadResearchMarkdown(run)}>
                        Download .md
                      </Button>
                    )}
                    {run.status === "failed" && (
                      <Box component="span" sx={{ color: "error.main" }}>
                        {run.error_message}
                      </Box>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      color="error"
                      disabled={deleteResearch.isPending}
                      onClick={() => handleDelete(run)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {research.data.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8}>No research runs yet.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
}
