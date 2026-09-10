import {
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
  Typography,
} from "@mui/material";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";
import type { ResearchResponse } from "../api/types";
import { downloadResearchMarkdown } from "../utils/downloadResearch";

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
