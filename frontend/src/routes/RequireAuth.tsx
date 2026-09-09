import { AppBar, Box, Button, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { useLogout } from "../hooks/useAuth";

// Layout route: wraps every authenticated page. Redirects to /login before any
// authenticated API call is made if there's no token stored (AC-5). A 401 on any
// later API call clears the token (see api/client.ts), which re-renders this and
// redirects the same way (AC-6). Also owns the nav bar, since it's only ever shown
// once the user is authenticated.
export function RequireAuth() {
  const token = useAuthStore((s) => s.token);
  const logout = useLogout();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      <AppBar position="static">
        <Toolbar sx={{ gap: 2 }}>
          <Button component={RouterLink} to="/agents" color="inherit">
            Agents
          </Button>
          <Button component={RouterLink} to="/agents/new" color="inherit">
            New agent
          </Button>
          <Button component={RouterLink} to="/research" color="inherit">
            Research
          </Button>
          <Button component={RouterLink} to="/research/new" color="inherit">
            New research
          </Button>
          <Typography sx={{ flexGrow: 1 }} />
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      <Box>
        <Outlet />
      </Box>
    </>
  );
}
