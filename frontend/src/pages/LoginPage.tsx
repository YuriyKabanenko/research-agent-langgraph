import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Alert, Box, Button, Container, Link, Stack, TextField, Typography } from "@mui/material";
import { useLogin } from "../hooks/useAuth";
import { ApiError } from "../api/client";

export function LoginPage() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const login = useLogin();
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    login.mutate({ name, password }, { onSuccess: () => navigate("/agents") });
  }

  return (
    <Container maxWidth="xs">
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 8 }}>
        <Stack spacing={2}>
          <Typography variant="h5">Log in</Typography>
          {login.isError && (
            <Alert severity="error">
              {login.error instanceof ApiError ? login.error.detail : "Login failed"}
            </Alert>
          )}
          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" variant="contained" disabled={login.isPending}>
            Log in
          </Button>
          <Typography variant="body2">
            Don't have an account?{" "}
            <Link component={RouterLink} to="/register">
              Register
            </Link>
          </Typography>
        </Stack>
      </Box>
    </Container>
  );
}
