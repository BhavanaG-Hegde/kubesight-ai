import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { FormEvent, useState } from "react";
import type { ReactNode } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../features/auth/useAuth";

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/dashboard";

  if (isAuthenticated) {
    return <Navigate replace to="/dashboard" />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to log in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFrame>
      <Card variant="outlined" sx={{ width: "100%", maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack spacing={3}>
            <Stack spacing={1} sx={{ alignItems: "center" }}>
              <LockOutlinedIcon color="primary" fontSize="large" />
              <Typography variant="h1">KubeSight AI</Typography>
            </Stack>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              <TextField
                autoComplete="email"
                label="Email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
              <TextField
                autoComplete="current-password"
                label="Password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
              <Button disabled={isSubmitting} size="large" type="submit" variant="contained">
                Log in
              </Button>
            </Stack>
            <Typography color="text.secondary" textAlign="center" variant="body2">
              <Link to="/register">Create account</Link>
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </AuthFrame>
  );
}

function AuthFrame({ children }: { children: ReactNode }) {
  return (
    <Box
      sx={{
        alignItems: "center",
        background:
          "linear-gradient(135deg, rgba(15,118,110,0.10), rgba(69,90,153,0.08))",
        display: "flex",
        justifyContent: "center",
        minHeight: "100vh",
        p: 2,
      }}
    >
      {children}
    </Box>
  );
}
