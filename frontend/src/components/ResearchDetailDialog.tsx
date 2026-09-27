import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";
import ReplayRoundedIcon from "@mui/icons-material/ReplayRounded";
import { ApiError } from "../api/client";
import type { ResearchResponse } from "../api/types";
import { downloadResearchMarkdown } from "../utils/downloadResearch";
import { useReviewResearch } from "../hooks/useResearch";

interface ResearchDetailDialogProps {
  run: ResearchResponse | null;
  onClose: () => void;
}

export function ResearchDetailDialog({ run, onClose }: ResearchDetailDialogProps) {
  return (
    <Dialog open={run != null} onClose={onClose} maxWidth="md" fullWidth>
      {run && (
        <>
          <DialogTitle sx={{ pr: 7 }}>
            {run.topic}
            <IconButton
              onClick={onClose}
              sx={{ position: "absolute", right: 12, top: 12 }}
              aria-label="Close"
            >
              <CloseRoundedIcon fontSize="small" />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            <Stack direction="row" spacing={1} useFlexGap sx={{ mb: 2, flexWrap: "wrap" }}>
              <Chip size="small" label={`Agent: ${run.agent_name}`} variant="outlined" />
              {run.research_rate != null && (
                <Chip size="small" label={`Rate: ${run.research_rate}/10`} color="success" variant="outlined" />
              )}
              <Chip
                size="small"
                label={new Date(run.created_at).toLocaleString()}
                variant="outlined"
              />
            </Stack>
            {run.tools_used && run.tools_used.length > 0 && (
              <>
                <Stack direction="row" spacing={0.75} useFlexGap sx={{ mb: 2, flexWrap: "wrap" }}>
                  {run.tools_used.map((tool) => (
                    <Chip key={tool} size="small" label={tool} />
                  ))}
                </Stack>
                <Divider sx={{ mb: 2 }} />
              </>
            )}
            {run.status === "awaiting_review" && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                This is a draft waiting for your review. Approve it to make it the final result, or send
                it back with feedback for another revision.
              </Alert>
            )}
            {run.status === "running" && run.research && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Showing the last draft - the run is still in progress. Refresh the list to check for
                updates.
              </Alert>
            )}
            {run.status === "failed" ? (
              <Typography color="error.main">{run.error_message}</Typography>
            ) : (
              <Box
                sx={{
                  whiteSpace: "pre-wrap",
                  fontSize: "0.9rem",
                  lineHeight: 1.7,
                  overflowWrap: "anywhere",
                }}
              >
                {run.research ?? "No content yet."}
              </Box>
            )}
            {/* Keyed by run so feedback typed for one run never carries over to another. */}
            {run.status === "awaiting_review" && <ReviewPanel key={run.id} researchId={run.id} />}
          </DialogContent>
          <DialogActions sx={{ px: 3, py: 1.5 }}>
            {run.status === "completed" && (
              <Button
                startIcon={<DownloadRoundedIcon fontSize="small" />}
                onClick={() => downloadResearchMarkdown(run)}
              >
                Download .md
              </Button>
            )}
            <Button onClick={onClose} variant="contained">
              Close
            </Button>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
}

function ReviewPanel({ researchId }: { researchId: string }) {
  const review = useReviewResearch(researchId);
  const [feedback, setFeedback] = useState("");
  const hasFeedback = feedback.trim().length > 0;

  return (
    <Box sx={{ mt: 3 }}>
      <Divider sx={{ mb: 2 }} />
      <TextField
        label="Feedback for the next revision"
        placeholder="What should be fixed, added, or dug into deeper?"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        disabled={review.isPending}
        multiline
        minRows={3}
        fullWidth
      />
      {review.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {review.error instanceof ApiError ? review.error.detail : "Failed to submit review"}
        </Alert>
      )}
      <Stack direction="row" spacing={1} useFlexGap sx={{ mt: 2, justifyContent: "flex-end", flexWrap: "wrap" }}>
        <Button
          startIcon={<ReplayRoundedIcon fontSize="small" />}
          disabled={!hasFeedback || review.isPending}
          onClick={() => review.mutate({ approved: false, feedback: feedback.trim() })}
        >
          Send back
        </Button>
        <Button
          variant="contained"
          color="success"
          startIcon={<CheckRoundedIcon fontSize="small" />}
          disabled={review.isPending}
          onClick={() => review.mutate({ approved: true })}
        >
          Approve
        </Button>
      </Stack>
    </Box>
  );
}
