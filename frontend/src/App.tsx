import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline } from "@mui/material";
import { Navigate, Route, BrowserRouter, Routes } from "react-router-dom";
import { RequireAuth } from "./routes/RequireAuth";
import { useAuthToken } from "./hooks/useAuth";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { AgentsPage } from "./pages/AgentsPage";
import { NewAgentPage } from "./pages/NewAgentPage";
import { ConfigureAgentPage } from "./pages/ConfigureAgentPage";
import { NewResearchPage } from "./pages/NewResearchPage";
import { ResearchesPage } from "./pages/ResearchesPage";

const queryClient = new QueryClient();

function RootRedirect() {
  const token = useAuthToken();
  return <Navigate to={token ? "/agents" : "/login"} replace />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route element={<RequireAuth />}>
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/agents/new" element={<NewAgentPage />} />
            <Route path="/agents/:agentId/config" element={<ConfigureAgentPage />} />
            <Route path="/research" element={<ResearchesPage />} />
            <Route path="/research/new" element={<NewResearchPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
