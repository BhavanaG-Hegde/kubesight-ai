import AnalyticsOutlinedIcon from "@mui/icons-material/AnalyticsOutlined";
import MemoryOutlinedIcon from "@mui/icons-material/MemoryOutlined";
import RestartAltOutlinedIcon from "@mui/icons-material/RestartAltOutlined";
import SpeedOutlinedIcon from "@mui/icons-material/SpeedOutlined";
import SyncOutlinedIcon from "@mui/icons-material/SyncOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getAnalyticsOverview } from "../api/analytics";
import { collectMetrics } from "../api/metrics";
import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import type {
  DistributionBucket,
  ClusterResourceTrendPoint,
  IncidentTrendPoint,
  PodResourcePoint,
  TopFailingPod,
} from "../types/domain";

const statusColors: Record<string, string> = {
  acknowledged: "#2563eb",
  critical: "#dc2626",
  info: "#0891b2",
  open: "#ea580c",
  resolved: "#16a34a",
  warning: "#d97706",
};

const chartColors = ["#0f766e", "#2563eb", "#d97706", "#dc2626", "#7c3aed", "#0891b2"];

export function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [collectionMessage, setCollectionMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const analyticsQuery = useQuery({
    queryKey: ["analytics-overview", days],
    queryFn: () => getAnalyticsOverview(days),
    refetchInterval: 60_000,
  });
  const collectMutation = useMutation({
    mutationFn: collectMetrics,
    onSuccess: async (response) => {
      setCollectionMessage(
        `Collected ${response.persisted_pod_metrics} pod metric samples from `
          + `${response.total_pods} pods.`,
      );
      await queryClient.invalidateQueries({ queryKey: ["analytics-overview"] });
    },
  });

  const overview = analyticsQuery.data;
  const trendData = useMemo(
    () => overview?.incident_trends.map(formatTrendPoint) ?? [],
    [overview?.incident_trends],
  );
  const topFailingPods = useMemo(
    () => overview?.top_failing_pods.map(formatFailingPod) ?? [],
    [overview?.top_failing_pods],
  );
  const topCpuPods = useMemo(
    () => overview?.top_cpu_pods.map(formatPodResource) ?? [],
    [overview?.top_cpu_pods],
  );
  const topMemoryPods = useMemo(
    () => overview?.top_memory_pods.map(formatPodResource) ?? [],
    [overview?.top_memory_pods],
  );
  const topRestartingPods = useMemo(
    () => overview?.top_restarting_pods.map(formatPodResource) ?? [],
    [overview?.top_restarting_pods],
  );
  const resourceTrendData = useMemo(
    () => overview?.resource_trends.map(formatResourceTrendPoint) ?? [],
    [overview?.resource_trends],
  );

  return (
    <Stack spacing={3}>
      <PageHeader
        actions={
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25}>
            <Button
              disabled={collectMutation.isPending}
              onClick={() => collectMutation.mutate()}
              startIcon={<SyncOutlinedIcon />}
              variant="contained"
            >
              {collectMutation.isPending ? "Collecting" : "Collect"}
            </Button>
            <FormControl size="small" sx={{ minWidth: 132 }}>
              <InputLabel id="analytics-window-label">Window</InputLabel>
              <Select
                label="Window"
                labelId="analytics-window-label"
                onChange={(event) => setDays(Number(event.target.value))}
                value={days}
              >
                <MenuItem value={7}>7 days</MenuItem>
                <MenuItem value={30}>30 days</MenuItem>
                <MenuItem value={90}>90 days</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        }
        subtitle="Incident history and workload risk patterns"
        title="Analytics"
      />

      {collectionMessage ? <Alert severity="success">{collectionMessage}</Alert> : null}
      {collectMutation.error ? (
        <Alert severity="warning">{String(collectMutation.error.message)}</Alert>
      ) : null}

      {analyticsQuery.isLoading ? (
        <Box sx={{ display: "grid", minHeight: 260, placeItems: "center" }}>
          <CircularProgress />
        </Box>
      ) : analyticsQuery.error ? (
        <Alert severity="warning">{String(analyticsQuery.error.message)}</Alert>
      ) : overview ? (
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
              icon={<AnalyticsOutlinedIcon color="primary" />}
              label="Incidents"
              value={overview.total_incidents}
            />
            <MetricCard
              icon={<WarningAmberOutlinedIcon color="warning" />}
              label="Open"
              value={overview.open_incidents}
            />
            <MetricCard
              icon={<WarningAmberOutlinedIcon color="error" />}
              label="Critical"
              value={overview.critical_incidents}
            />
            <MetricCard
              helper={`${overview.days} day window`}
              icon={<RestartAltOutlinedIcon color="success" />}
              label="Resolved"
              value={overview.resolved_incidents}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", xl: "1.25fr 1fr" },
            }}
          >
            <ChartCard title="Incident Trends">
              {trendData.some((point) => point.total > 0) ? (
                <ResponsiveContainer height="100%" width="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="dateLabel" minTickGap={20} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Line dataKey="critical" dot={false} stroke="#dc2626" strokeWidth={2} />
                    <Line dataKey="warning" dot={false} stroke="#d97706" strokeWidth={2} />
                    <Line dataKey="info" dot={false} stroke="#0891b2" strokeWidth={2} />
                    <Line dataKey="total" dot={false} stroke="#0f766e" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState title="No incident trend data yet." />
              )}
            </ChartCard>

            <ChartCard title="Severity Distribution">
              <DistributionPie data={overview.severity_distribution} />
            </ChartCard>
          </Box>

          <ChartCard title="Resource Trends">
            {resourceTrendData.length > 0 ? (
              <ResponsiveContainer height="100%" width="100%">
                <LineChart data={resourceTrendData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="timeLabel" minTickGap={18} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Line dataKey="cpu_millicores" dot={false} stroke="#2563eb" strokeWidth={2} />
                  <Line dataKey="memory_mebibytes" dot={false} stroke="#0f766e" strokeWidth={2} />
                  <Line dataKey="restart_count" dot={false} stroke="#d97706" strokeWidth={2} />
                  <Line dataKey="health_score" dot={false} stroke="#16a34a" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="Collect metrics to build resource trends." />
            )}
          </ChartCard>

          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" },
            }}
          >
            <ChartCard title="Error Distribution">
              <DistributionBar data={overview.incident_type_distribution} />
            </ChartCard>
            <ChartCard title="Incident Status">
              <DistributionBar data={overview.status_distribution} />
            </ChartCard>
          </Box>

          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" },
            }}
          >
            <ChartCard title="Top Failing Pods">
              {topFailingPods.length > 0 ? (
                <ResponsiveContainer height="100%" width="100%">
                  <BarChart data={topFailingPods} layout="vertical" margin={{ left: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis allowDecimals={false} type="number" />
                    <YAxis dataKey="label" type="category" width={160} />
                    <Tooltip />
                    <Bar dataKey="incident_count" fill="#dc2626" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState title="No failing pods yet." />
              )}
            </ChartCard>
            <ChartCard title="Restart Counts">
              <ResourceBar data={topRestartingPods} dataKey="restart_count" fill="#d97706" />
            </ChartCard>
          </Box>

          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" },
            }}
          >
            <ChartCard icon={<SpeedOutlinedIcon color="primary" />} title="CPU Usage">
              <ResourceBar data={topCpuPods} dataKey="cpu_millicores" fill="#2563eb" />
            </ChartCard>
            <ChartCard icon={<MemoryOutlinedIcon color="primary" />} title="Memory Usage">
              <ResourceBar data={topMemoryPods} dataKey="memory_mebibytes" fill="#0f766e" />
            </ChartCard>
          </Box>
        </>
      ) : null}
    </Stack>
  );
}

function ChartCard({
  children,
  icon,
  title,
}: {
  children: ReactNode;
  icon?: ReactNode;
  title: string;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
            {icon}
            <Typography variant="h3">{title}</Typography>
          </Stack>
          <Box sx={{ height: 320 }}>{children}</Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

function DistributionPie({ data }: { data: DistributionBucket[] }) {
  if (data.length === 0) {
    return <EmptyState title="No severity counts yet." />;
  }

  return (
    <ResponsiveContainer height="100%" width="100%">
      <PieChart>
        <Pie data={data} dataKey="value" innerRadius={64} nameKey="label" outerRadius={104}>
          {data.map((entry, index) => (
            <Cell
              fill={statusColors[entry.label] ?? chartColors[index % chartColors.length]}
              key={entry.label}
            />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

function DistributionBar({ data }: { data: DistributionBucket[] }) {
  if (data.length === 0) {
    return <EmptyState title="No incidents have been stored yet." />;
  }

  return (
    <ResponsiveContainer height="100%" width="100%">
      <BarChart data={data.map((item) => ({ ...item, label: formatLabel(item.label) }))}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" interval={0} tick={{ fontSize: 12 }} />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="value" fill="#0f766e" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ResourceBar({
  data,
  dataKey,
  fill,
}: {
  data: Array<PodResourcePoint & { label: string }>;
  dataKey: keyof PodResourcePoint;
  fill: string;
}) {
  if (data.length === 0) {
    return <EmptyState title="No pod resource samples yet." />;
  }

  return (
    <ResponsiveContainer height="100%" width="100%">
      <BarChart data={data} layout="vertical" margin={{ left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis allowDecimals={false} type="number" />
        <YAxis dataKey="label" type="category" width={160} />
        <Tooltip />
        <Bar dataKey={dataKey} fill={fill} radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function formatTrendPoint(point: IncidentTrendPoint) {
  const date = new Date(`${point.date}T00:00:00`);
  return {
    ...point,
    dateLabel: date.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
  };
}

function formatResourceTrendPoint(point: ClusterResourceTrendPoint) {
  const sampledAt = new Date(point.sampled_at);
  return {
    ...point,
    timeLabel: sampledAt.toLocaleString(undefined, {
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      month: "short",
    }),
  };
}

function formatFailingPod(point: TopFailingPod) {
  return {
    ...point,
    label: compactPodLabel(point.namespace, point.pod_name),
  };
}

function formatPodResource(point: PodResourcePoint) {
  return {
    ...point,
    label: compactPodLabel(point.namespace, point.pod_name),
  };
}

function compactPodLabel(namespace?: string | null, podName?: string | null): string {
  if (!namespace && !podName) {
    return "cluster";
  }
  if (!namespace) {
    return podName ?? "unknown";
  }
  if (!podName) {
    return namespace;
  }
  return `${namespace}/${podName}`;
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
