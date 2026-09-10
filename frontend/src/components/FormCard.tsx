import { Avatar, Container, Paper, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface FormCardProps {
  icon: ReactNode;
  title: string;
  description?: string;
  maxWidth?: number;
  children: ReactNode;
}

// Consistent centered-card chrome for every standalone form page (new/edit agent,
// agent config, new research) so they read as one family instead of ad hoc layouts.
export function FormCard({ icon, title, description, maxWidth = 480, children }: FormCardProps) {
  return (
    <Container disableGutters sx={{ display: "flex", justifyContent: "center", py: { xs: 2, md: 4 } }}>
      <Paper variant="outlined" sx={{ p: { xs: 3, sm: 4 }, width: "100%", maxWidth }}>
        <Stack direction="row" spacing={1.75} sx={{ mb: 3, alignItems: "center" }}>
          <Avatar sx={{ bgcolor: "primary.main", width: 44, height: 44 }}>{icon}</Avatar>
          <Stack spacing={0.25}>
            <Typography variant="h6">{title}</Typography>
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
          </Stack>
        </Stack>
        {children}
      </Paper>
    </Container>
  );
}
