import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import type { ChipProps } from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import { useDeleteResearch, useResearches } from "../hooks/useResearch";
import { ApiError } from "../api/client";
import type { ResearchResponse, ResearchStatus } from "../api/types";
import { PageHeader } from "../components/PageHeader";
import { EmptyState } from "../components/EmptyState";
import { useConfirm } from "../components/ConfirmDialogProvider";
import { ResearchDetailDialog } from "../components/ResearchDetailDialog";

const STATUS_COLOR: Record<ResearchStatus, ChipProps["color"]> = {
  pending: "default",
  running: "info",
  completed: "success",
  failed: "error",
};

export function ResearchesPage() {
  const research = useResearches();
  const deleteResearch = useDeleteResearch();
  const confirm = useConfirm();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [viewing, setViewing] = useState<ResearchResponse | null>(null);

  async function handleDelete(run: ResearchResponse) {
    const ok = await confirm({
      title: `Delete "${run.topic}"?`,
      description: "This research run and its result will be permanently removed.",
      confirmText: "Delete",
      danger: true,
    });
    if (ok) deleteResearch.mutate(run.id);
  }

  const rows = research.data ?? [];

  return (
    <Box>
      <PageHeader
        title="Research"
        description="Every run this account has started, newest results included."
        action={
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh">
              <span>
                <IconButton onClick={() => research.refetch()} disabled={research.isFetching}>
                  <RefreshRoundedIcon />
                </IconButton>
              </span>
            </Tooltip>
            <Button component={RouterLink} to="/research/new" variant="contained" startIcon={<AddRoundedIcon />}>
              New research
            </Button>
          </Stack>
        }
      />

      {research.isLoading && (
        <Stack sx={{ alignItems: "center", py: 8 }}>
          <CircularProgress />
        </Stack>
      )}
      {research.isError && <Alert severity="error">Failed to load research runs.</Alert>}
      {deleteResearch.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {deleteResearch.error instanceof ApiError ? deleteResearch.error.detail : "Failed to delete research"}
        </Alert>
      )}

      {research.isSuccess && rows.length === 0 && (
        <EmptyState
          icon={<TravelExploreOutlinedIcon />}
          title="No research runs yet"
          description="Pick a configured agent and give it a topic to research."
          action={
            <Button component={RouterLink} to="/research/new" variant="contained" startIcon={<AddRoundedIcon />}>
              Start research
            </Button>
          }
        />
      )}

      {research.isSuccess && rows.length > 0 && isDesktop && (
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Topic</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Rate</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell sx={{ maxWidth: 280, overflowWrap: "anywhere" }}>{run.topic}</TableCell>
                  <TableCell>{run.agent_name}</TableCell>
                  <TableCell>
                    <Chip label={run.status} color={STATUS_COLOR[run.status]} size="small" />
                  </TableCell>
                  <TableCell>{run.research_rate != null ? `${run.research_rate}/10` : "—"}</TableCell>
                  <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
                      <Tooltip title="View details">
                        <IconButton size="small" onClick={() => setViewing(run)}>
                          <VisibilityOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          disabled={deleteResearch.isPending}
                          onClick={() => handleDelete(run)}
                        >
                          <DeleteOutlineRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {research.isSuccess && rows.length > 0 && !isDesktop && (
        <Stack spacing={1.5}>
          {rows.map((run) => (
            <Card key={run.id} variant="outlined">
              <CardContent>
                <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                  <Typography variant="subtitle2" sx={{ overflowWrap: "anywhere" }}>
                    {run.topic}
                  </Typography>
                  <Chip label={run.status} color={STATUS_COLOR[run.status]} size="small" />
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {run.agent_name} · {new Date(run.created_at).toLocaleDateString()}
                  {run.research_rate != null ? ` · ${run.research_rate}/10` : ""}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                  <Button size="small" startIcon={<VisibilityOutlinedIcon fontSize="small" />} onClick={() => setViewing(run)}>
                    View
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    disabled={deleteResearch.isPending}
                    startIcon={<DeleteOutlineRoundedIcon fontSize="small" />}
                    onClick={() => handleDelete(run)}
                  >
                    Delete
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      <ResearchDetailDialog run={viewing} onClose={() => setViewing(null)} />
    </Box>
  );
}
