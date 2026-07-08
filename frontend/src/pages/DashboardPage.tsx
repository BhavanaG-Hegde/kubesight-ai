import MemoryOutlinedIcon from "@mui/icons-material/MemoryOutlined";
import RestartAltOutlinedIcon from "@mui/icons-material/RestartAltOutlined";
import RunningWithErrorsOutlinedIcon from "@mui/icons-material/RunningWithErrorsOutlined";
import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getClusterSummary } from "../api/kubernetes";
import { getIncidents } from "../api/incidents";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { StatusChip } from "../components/StatusChip";
import { formatDateTime } from "../utils/format";

export function DashboardPage() {
  const summaryQuery = useQuery({
    queryKey: ["cluster-summary"],
    queryFn: getClusterSummary,
    refetchInterval: 30_000,
  });
  const incidentsQuery = useQuery({
    queryKey: ["incidents", "dashboard"],
    queryFn: () => getIncidents({}),
  });

  const summary = summaryQuery.data;
  const incidents = incidentsQuery.data?.items ?? [];
  const openIncidents = incidents.filter((incident) => incident.status === "open").length;
  const criticalIncidents = incidents.filter((incident) => incident.severity === "critical").length;
  const healthScore = summary ? calculateHealthScore(summary.failed_pods, summary.total_pods) : "—";

  const podChartData = summary
    ? [
        { name: "Running", value: summary.running_pods },
        { name: "Pending", value: summary.pending_pods },
        { name: "Failed", value: summary.failed_pods },
      ]
    : [];

  return (
    <Stack spacing={3}>
      <PageHeader title="Cluster Dashboard" subtitle="Live Kubernetes health overview" />

      {summaryQuery.isLoading ? (
        <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
          <CircularProgress />
        </Box>
      ) : summaryQuery.error ? (
        <Alert severity="warning">{String(summaryQuery.error.message)}</Alert>
      ) : (
        <>
          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: {
                xs: "1fr",
                sm: "repeat(2, minmax(0, 1fr))",
                lg: "repeat(4, minmax(0, 1fr))",
              },
            }}
          >
            <MetricCard
              icon={<StorageOutlinedIcon color="primary" />}
              label="Total Pods"
              value={summary?.total_pods ?? "—"}
            />
            <MetricCard
              icon={<RunningWithErrorsOutlinedIcon color="success" />}
              label="Running Pods"
              value={summary?.running_pods ?? "—"}
            />
            <MetricCard
              icon={<RestartAltOutlinedIcon color="warning" />}
              label="Restarts"
              value={summary?.restart_count ?? "—"}
            />
            <MetricCard
              helper="Rule-based"
              icon={<MemoryOutlinedIcon color="primary" />}
              label="Health Score"
              value={healthScore}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", lg: "1.35fr 1fr" },
            }}
          >
            <Card variant="outlined">
              <CardContent>
                <Typography gutterBottom variant="h3">
                  Pod Distribution
                </Typography>
                <Box sx={{ height: 280 }}>
                  <ResponsiveContainer height="100%" width="100%">
                    <BarChart data={podChartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0f766e" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                    <WarningAmberOutlinedIcon color="warning" />
                    <Typography variant="h3">Incident Snapshot</Typography>
                  </Stack>
                  <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: "1fr 1fr" }}>
                    <SnapshotMetric label="Open" value={openIncidents} />
                    <SnapshotMetric label="Critical" value={criticalIncidents} />
                  </Box>
                  <Stack spacing={1.2}>
                    {incidents.slice(0, 5).map((incident) => (
                      <Stack
                        direction="row"
                        key={incident.id}
                        spacing={1}
                        sx={{ alignItems: "center", justifyContent: "space-between" }}
                      >
                        <Box sx={{ minWidth: 0 }}>
                          <Typography noWrap variant="body2">
                            {incident.title}
                          </Typography>
                          <Typography color="text.secondary" variant="caption">
                            {formatDateTime(incident.last_seen_at)}
                          </Typography>
                        </Box>
                        <StatusChip value={incident.severity} />
                      </Stack>
                    ))}
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Box>
        </>
      )}
    </Stack>
  );
}

function calculateHealthScore(failedPods: number, totalPods: number): number {
  if (totalPods === 0) {
    return 100;
  }
  return Math.max(0, Math.round(100 - (failedPods / totalPods) * 100));
}

function SnapshotMetric({ label, value }: { label: string; value: number }) {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        p: 1.5,
      }}
    >
      <Typography color="text.secondary" variant="caption">
        {label}
      </Typography>
      <Typography variant="h3">{value}</Typography>
    </Box>
  );
}
