import PersonAddAltOutlinedIcon from "@mui/icons-material/PersonAddAltOutlined";
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
import { Link, Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../features/auth/useAuth";

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate replace to="/dashboard" />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(fullName, email, password);
      navigate("/dashboard", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to register.");
    } finally {
      setIsSubmitting(false);
    }
  }

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
      <Card variant="outlined" sx={{ width: "100%", maxWidth: 460 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack spacing={3}>
            <Stack spacing={1} sx={{ alignItems: "center" }}>
              <PersonAddAltOutlinedIcon color="primary" fontSize="large" />
              <Typography variant="h1">Create Account</Typography>
            </Stack>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              <TextField
                autoComplete="name"
                label="Full name"
                onChange={(event) => setFullName(event.target.value)}
                required
                value={fullName}
              />
              <TextField
                autoComplete="email"
                label="Email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
              <TextField
                autoComplete="new-password"
                label="Password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
              <Button disabled={isSubmitting} size="large" type="submit" variant="contained">
                Register
              </Button>
            </Stack>
            <Typography color="text.secondary" textAlign="center" variant="body2">
              <Link to="/login">Log in</Link>
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
