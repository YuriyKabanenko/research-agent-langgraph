import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  IconButton,
  InputAdornment,
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import PersonOutlineRoundedIcon from "@mui/icons-material/PersonOutlineRounded";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import VisibilityOffRoundedIcon from "@mui/icons-material/VisibilityOffRounded";
import { useRegister } from "../hooks/useAuth";
import { ApiError } from "../api/client";
import { AuthLayout } from "../components/AuthLayout";

export function RegisterPage() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const register = useRegister();
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    register.mutate({ name, password }, { onSuccess: () => navigate("/agents") });
  }

  return (
    <AuthLayout title="Create an account" subtitle="Set up agents and start researching in minutes.">
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <Stack spacing={2.25}>
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
            autoFocus
            helperText="1–50 characters"
            slotProps={{
              htmlInput: { minLength: 1, maxLength: 50 },
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonOutlineRoundedIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
          />
          <TextField
            label="Password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            helperText="6–100 characters"
            slotProps={{
              htmlInput: { minLength: 6, maxLength: 100 },
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <LockOutlinedIcon fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword((v) => !v)}
                      edge="end"
                      size="small"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? (
                        <VisibilityOffRoundedIcon fontSize="small" />
                      ) : (
                        <VisibilityRoundedIcon fontSize="small" />
                      )}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />
          <Button type="submit" variant="contained" size="large" disabled={register.isPending}>
            {register.isPending ? "Creating account…" : "Register"}
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
            Already have an account?{" "}
            <Link component={RouterLink} to="/login" sx={{ fontWeight: 600 }}>
              Log in
            </Link>
          </Typography>
        </Stack>
      </Box>
    </AuthLayout>
  );
}
