import { Box, Paper, Stack, Typography } from "@mui/material";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import TravelExploreRoundedIcon from "@mui/icons-material/TravelExploreRounded";
import FactCheckRoundedIcon from "@mui/icons-material/FactCheckRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import type { ReactNode } from "react";

const FEATURES = [
  { icon: TravelExploreRoundedIcon, text: "Real web search backs every research run" },
  { icon: FactCheckRoundedIcon, text: "Self-critiques its own draft before it settles" },
  { icon: AutoAwesomeRoundedIcon, text: "Bring your own key for Claude, GPT, or Gemini" },
];

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

// Shared shell for Login/Register: a brand panel (hidden below md) plus a centered
// card for the form, so both auth pages read as one polished flow rather than two
// bare forms on a blank page.
export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "stretch",
      }}
    >
      <Box
        sx={{
          display: { xs: "none", md: "flex" },
          flexDirection: "column",
          justifyContent: "center",
          width: "42%",
          px: 6,
          color: "primary.contrastText",
          background: (t) =>
            `linear-gradient(160deg, ${t.palette.primary.dark}, ${t.palette.primary.main})`,
        }}
      >
        <Stack direction="row" spacing={1.25} sx={{ mb: 4, alignItems: "center" }}>
          <HubRoundedIcon fontSize="large" />
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Research Assistant
          </Typography>
        </Stack>
        <Typography variant="h4" sx={{ mb: 2, maxWidth: 420 }}>
          Self-checking research, on demand.
        </Typography>
        <Typography sx={{ opacity: 0.85, mb: 5, maxWidth: 420 }}>
          Give it a topic. It drafts an answer, critiques itself, and loops back to research
          again until the result clears the bar you set.
        </Typography>
        <Stack spacing={2.5}>
          {FEATURES.map(({ icon: Icon, text }) => (
            <Stack key={text} direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
              <Icon fontSize="small" />
              <Typography variant="body2" sx={{ opacity: 0.92 }}>
                {text}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </Box>

      <Box
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          p: { xs: 2, sm: 4 },
        }}
      >
        <Paper
          variant="outlined"
          sx={{ p: { xs: 3, sm: 4.5 }, width: "100%", maxWidth: 400 }}
        >
          <Stack spacing={0.5} sx={{ mb: 3 }}>
            <Typography variant="h5">{title}</Typography>
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          </Stack>
          {children}
        </Paper>
      </Box>
    </Box>
  );
}
