import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { analyzeIncident, askAI, getAIAnalyses } from "../api/ai";
import { getIncident, updateIncident } from "../api/incidents";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusChip } from "../components/StatusChip";
import type { IncidentStatus } from "../types/domain";
import { formatDateTime, titleCase } from "../utils/format";

const statusOptions: IncidentStatus[] = ["open", "acknowledged", "resolved"];

export function IncidentDetailPage() {
  const { incidentId = "" } = useParams();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<IncidentStatus>("open");
  const [rootCause, setRootCause] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [resolution, setResolution] = useState("");
  const [question, setQuestion] = useState("");

  const incidentQuery = useQuery({
    enabled: Boolean(incidentId),
    queryKey: ["incident", incidentId],
    queryFn: () => getIncident(incidentId),
  });
  const analysesQuery = useQuery({
    enabled: Boolean(incidentId),
    queryKey: ["ai-analyses", "incident", incidentId],
    queryFn: () => getAIAnalyses(incidentId),
  });

  const incident = incidentQuery.data;
  const analyses = analysesQuery.data?.items ?? [];
  const latestAnalysis = analyses[0];

  useEffect(() => {
    if (!incident) {
      return;
    }
    setStatus(incident.status);
    setRootCause(incident.root_cause ?? "");
    setRecommendation(incident.recommendation ?? "");
    setResolution(incident.resolution ?? "");
  }, [incident]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateIncident(incidentId, {
        status,
        root_cause: rootCause,
        recommendation,
        resolution,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["incident", incidentId] }),
        queryClient.invalidateQueries({ queryKey: ["incidents"] }),
      ]);
    },
  });
  const resolveMutation = useMutation({
    mutationFn: () =>
      updateIncident(incidentId, {
        status: "resolved",
        root_cause: rootCause,
        recommendation,
        resolution: resolution || "Resolved from KubeSight AI.",
      }),
    onSuccess: async () => {
      setStatus("resolved");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["incident", incidentId] }),
        queryClient.invalidateQueries({ queryKey: ["incidents"] }),
      ]);
    },
  });
  const analyzeMutation = useMutation({
    mutationFn: () => analyzeIncident(incidentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ai-analyses", "incident", incidentId] });
    },
  });
  const askMutation = useMutation({
    mutationFn: () =>
      askAI({
        question,
        incident_id: incidentId,
        include_logs: true,
      }),
    onSuccess: async () => {
      setQuestion("");
      await queryClient.invalidateQueries({ queryKey: ["ai-analyses", "incident", incidentId] });
    },
  });

  const aiResponse =
    analyzeMutation.data?.response ?? askMutation.data?.response ?? latestAnalysis?.response;
  const incidentPodPath = useMemo(() => {
    if (!incident?.namespace || !incident.pod_name) {
      return null;
    }
    return `/namespaces/${encodeURIComponent(incident.namespace)}/pods/${encodeURIComponent(
      incident.pod_name,
    )}`;
  }, [incident?.namespace, incident?.pod_name]);

  if (incidentQuery.isLoading) {
    return <LoadingPanel />;
  }
  if (incidentQuery.error) {
    return <Alert severity="warning">{incidentQuery.error.message}</Alert>;
  }
  if (!incident) {
    return <EmptyState title="Incident not found." />;
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        actions={
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
            {incidentPodPath ? (
              <Button
                component={Link}
                startIcon={<OpenInNewOutlinedIcon />}
                to={incidentPodPath}
                variant="outlined"
              >
                Pod
              </Button>
            ) : null}
            <Button
              component={Link}
              startIcon={<ArrowBackOutlinedIcon />}
              to="/incidents"
              variant="outlined"
            >
              Incidents
            </Button>
          </Stack>
        }
        subtitle={`${incident.namespace ?? "cluster"} / ${incident.pod_name ?? "all pods"}`}
        title={incident.title}
      />

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "1.25fr 0.75fr" },
        }}
      >
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={2}>
              <Typography variant="h3">Incident Summary</Typography>
              <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
                <StatusChip value={incident.severity} />
                <StatusChip value={incident.status} />
                <StatusChip value={incident.incident_type} />
              </Stack>
              <Typography sx={{ whiteSpace: "pre-wrap" }}>{incident.summary}</Typography>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1.5}>
              <Typography variant="h3">Timeline</Typography>
              <TimelineMetric label="First Seen" value={formatDateTime(incident.first_seen_at)} />
              <TimelineMetric label="Last Seen" value={formatDateTime(incident.last_seen_at)} />
              <TimelineMetric label="Resolved" value={formatDateTime(incident.resolved_at)} />
              <TimelineMetric label="Source" value={titleCase(incident.detection_source)} />
            </Stack>
          </CardContent>
        </Card>
      </Box>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h3">Resolution Notes</Typography>
            <Box
              sx={{
                display: "grid",
                gap: 2,
                gridTemplateColumns: { xs: "1fr", md: "220px 1fr" },
              }}
            >
              <TextField
                label="Status"
                onChange={(event) => setStatus(event.target.value as IncidentStatus)}
                select
                value={status}
              >
                {statusOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    {titleCase(option)}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Root Cause"
                multiline
                onChange={(event) => setRootCause(event.target.value)}
                rows={3}
                value={rootCause}
              />
              <Box />
              <TextField
                label="Recommendation"
                multiline
                onChange={(event) => setRecommendation(event.target.value)}
                rows={3}
                value={recommendation}
              />
              <Box />
              <TextField
                label="Resolution"
                multiline
                onChange={(event) => setResolution(event.target.value)}
                rows={3}
                value={resolution}
              />
            </Box>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
              <Button
                disabled={saveMutation.isPending}
                onClick={() => saveMutation.mutate()}
                startIcon={<SaveOutlinedIcon />}
                variant="contained"
              >
                Save
              </Button>
              <Button
                color="success"
                disabled={resolveMutation.isPending || incident.status === "resolved"}
                onClick={() => resolveMutation.mutate()}
                startIcon={<CheckCircleOutlineOutlinedIcon />}
                variant="outlined"
              >
                Resolve
              </Button>
            </Stack>
            {saveMutation.error ? (
              <Alert severity="warning">{saveMutation.error.message}</Alert>
            ) : null}
            {resolveMutation.error ? (
              <Alert severity="warning">{resolveMutation.error.message}</Alert>
            ) : null}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={1.5}>
              <Button
                disabled={analyzeMutation.isPending}
                onClick={() => analyzeMutation.mutate()}
                startIcon={<AutoAwesomeOutlinedIcon />}
                variant="contained"
              >
                Analyze
              </Button>
              <TextField
                fullWidth
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a follow-up question"
                size="small"
                value={question}
              />
              <Button
                disabled={question.trim().length < 3 || askMutation.isPending}
                onClick={() => askMutation.mutate()}
                variant="outlined"
              >
                Ask
              </Button>
            </Stack>
            {analyzeMutation.error ? (
              <Alert severity="warning">{analyzeMutation.error.message}</Alert>
            ) : null}
            {askMutation.error ? (
              <Alert severity="warning">{askMutation.error.message}</Alert>
            ) : null}
            {aiResponse ? (
              <Paper sx={{ p: 2 }} variant="outlined">
                <Typography sx={{ whiteSpace: "pre-wrap" }}>{aiResponse}</Typography>
              </Paper>
            ) : (
              <EmptyState title="Run AI analysis to generate root cause guidance." />
            )}
            <Divider />
            <Typography variant="h3">Analysis History</Typography>
            {analysesQuery.isLoading ? (
              <CircularProgress size={28} />
            ) : analyses.length > 0 ? (
              <Stack spacing={1.5}>
                {analyses.map((analysis) => (
                  <Paper key={analysis.id} sx={{ p: 1.5 }} variant="outlined">
                    <Typography color="text.secondary" variant="caption">
                      {formatDateTime(analysis.created_at)} / {analysis.model_name}
                    </Typography>
                    <Typography sx={{ mt: 0.75, whiteSpace: "pre-wrap" }} variant="body2">
                      {analysis.response}
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            ) : (
              <EmptyState title="No AI analyses saved for this incident yet." />
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

function TimelineMetric({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography color="text.secondary" variant="caption">
        {label}
      </Typography>
      <Typography>{value}</Typography>
    </Box>
  );
}

function LoadingPanel() {
  return (
    <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
      <CircularProgress />
    </Box>
  );
}
