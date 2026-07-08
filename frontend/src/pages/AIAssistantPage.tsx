import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { askAI } from "../api/ai";
import { PageHeader } from "../components/PageHeader";

export function AIAssistantPage() {
  const [question, setQuestion] = useState("");
  const [incidentId, setIncidentId] = useState("");
  const [namespace, setNamespace] = useState("");
  const [podName, setPodName] = useState("");
  const [includeLogs, setIncludeLogs] = useState(true);

  const askMutation = useMutation({
    mutationFn: askAI,
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    askMutation.mutate({
      question,
      incident_id: incidentId || undefined,
      namespace: namespace || undefined,
      pod_name: podName || undefined,
      include_logs: includeLogs,
    });
  }

  return (
    <Stack spacing={3}>
      <PageHeader title="AI Assistant" />
      <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "0.9fr 1.1fr" } }}>
        <Card variant="outlined">
          <CardContent>
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              <TextField
                label="Question"
                multiline
                minRows={4}
                onChange={(event) => setQuestion(event.target.value)}
                required
                value={question}
              />
              <TextField
                label="Incident ID"
                onChange={(event) => setIncidentId(event.target.value)}
                value={incidentId}
              />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                <TextField
                  fullWidth
                  label="Namespace"
                  onChange={(event) => setNamespace(event.target.value)}
                  value={namespace}
                />
                <TextField
                  fullWidth
                  label="Pod"
                  onChange={(event) => setPodName(event.target.value)}
                  value={podName}
                />
              </Stack>
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Switch
                  checked={includeLogs}
                  onChange={(event) => setIncludeLogs(event.target.checked)}
                />
                <Typography>Include logs</Typography>
              </Stack>
              <Button
                disabled={askMutation.isPending}
                endIcon={<SendOutlinedIcon />}
                type="submit"
                variant="contained"
              >
                Ask
              </Button>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent sx={{ minHeight: 420 }}>
            {askMutation.isPending ? (
              <Box sx={{ display: "grid", minHeight: 320, placeItems: "center" }}>
                <CircularProgress />
              </Box>
            ) : askMutation.error ? (
              <Alert severity="warning">{askMutation.error.message}</Alert>
            ) : askMutation.data ? (
              <Stack spacing={2}>
                <Typography variant="h3">{askMutation.data.model_name}</Typography>
                <Typography sx={{ whiteSpace: "pre-wrap" }}>
                  {askMutation.data.response}
                </Typography>
              </Stack>
            ) : (
              <Box sx={{ display: "grid", minHeight: 320, placeItems: "center" }}>
                <Typography color="text.secondary">No response yet</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    </Stack>
  );
}
