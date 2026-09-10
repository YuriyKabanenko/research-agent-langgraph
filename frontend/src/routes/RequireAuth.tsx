import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { useLogout } from "../hooks/useAuth";
import { AppShell } from "../components/AppShell";

// Layout route: wraps every authenticated page. Redirects to /login before any
// authenticated API call is made if there's no token stored (AC-5). A 401 on any
// later API call clears the token (see api/client.ts), which re-renders this and
// redirects the same way (AC-6). Also owns the app shell (nav + top bar), since it's
// only ever shown once the user is authenticated.
export function RequireAuth() {
  const token = useAuthStore((s) => s.token);
  const logout = useLogout();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppShell onLogout={logout}>
      <Outlet />
    </AppShell>
  );
}
