import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Alert, Box, Button, Container, Link, Stack, TextField, Typography } from "@mui/material";
import { useRegister } from "../hooks/useAuth";
import { ApiError } from "../api/client";

export function RegisterPage() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const register = useRegister();
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    register.mutate({ name, password }, { onSuccess: () => navigate("/agents") });
  }

  return (
    <Container maxWidth="xs">
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 8 }}>
        <Stack spacing={2}>
          <Typography variant="h5">Register</Typography>
          {register.isError && (
            <Alert severity="error">
              {register.error instanceof ApiError ? register.error.detail : "Registration failed"}
            </Alert>
          )}
          <TextField
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            slotProps={{ htmlInput: { minLength: 1, maxLength: 50 } }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            slotProps={{ htmlInput: { minLength: 6, maxLength: 100 } }}
          />
          <Button type="submit" variant="contained" disabled={register.isPending}>
            Register
          </Button>
          <Typography variant="body2">
            Already have an account?{" "}
            <Link component={RouterLink} to="/login">
              Log in
            </Link>
          </Typography>
        </Stack>
      </Box>
    </Container>
  );
}
