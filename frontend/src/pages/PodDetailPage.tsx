import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  InputAdornment,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getPod, getPodEvents, getPodHealth, getPodLogs } from "../api/kubernetes";
import { PageHeader } from "../components/PageHeader";
import { StatusChip } from "../components/StatusChip";
import { formatDateTime, titleCase } from "../utils/format";

const severityOptions = ["all", "error", "warning", "info"];

export function PodDetailPage() {
  const { namespace = "", podName = "" } = useParams();
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");

  const podQuery = useQuery({
    enabled: Boolean(namespace && podName),
    queryKey: ["pod", namespace, podName],
    queryFn: () => getPod(namespace, podName),
  });
  const healthQuery = useQuery({
    enabled: Boolean(namespace && podName),
    queryKey: ["pod-health", namespace, podName],
    queryFn: () => getPodHealth(namespace, podName),
  });
  const eventsQuery = useQuery({
    enabled: Boolean(namespace && podName),
    queryKey: ["pod-events", namespace, podName],
    queryFn: () => getPodEvents(namespace, podName),
  });
  const logsQuery = useQuery({
    enabled: Boolean(namespace && podName),
    queryKey: ["pod-logs", namespace, podName],
    queryFn: () => getPodLogs(namespace, podName),
  });

  const filteredLogs = useMemo(() => {
    const lines = logsQuery.data?.lines ?? [];
    return lines.filter((line) => {
      const normalized = line.toLowerCase();
      const matchesSearch = search ? normalized.includes(search.toLowerCase()) : true;
      const matchesSeverity = severity === "all" ? true : normalized.includes(severity);
      return matchesSearch && matchesSeverity;
    });
  }, [logsQuery.data?.lines, search, severity]);

  if (podQuery.isLoading) {
    return <LoadingPanel />;
  }
  if (podQuery.error) {
    return <Alert severity="warning">{podQuery.error.message}</Alert>;
  }

  const pod = podQuery.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        actions={
          <Button
            component={Link}
            startIcon={<ArrowBackOutlinedIcon />}
            to="/namespaces"
            variant="outlined"
          >
            Namespaces
          </Button>
        }
        subtitle={namespace}
        title={podName}
      />

      {pod ? (
        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" },
          }}
        >
          <Card variant="outlined">
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h3">Status</Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
                  <StatusChip value={pod.phase} />
                  <Typography color="text.secondary">
                    Ready {pod.ready_containers}/{pod.total_containers}
                  </Typography>
                  <Typography color="text.secondary">Restarts {pod.restart_count}</Typography>
                </Stack>
                <Divider />
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Container</TableCell>
                      <TableCell>State</TableCell>
                      <TableCell>Ready</TableCell>
                      <TableCell>Restarts</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pod.containers.map((container) => (
                      <TableRow key={container.name}>
                        <TableCell>{container.name}</TableCell>
                        <TableCell>
                          {titleCase(container.state)}
                          {container.reason ? ` · ${container.reason}` : ""}
                        </TableCell>
                        <TableCell>{container.ready ? "Yes" : "No"}</TableCell>
                        <TableCell>{container.restart_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Stack>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h3">Health</Typography>
                {healthQuery.isLoading ? (
                  <CircularProgress size={28} />
                ) : healthQuery.error ? (
                  <Alert severity="warning">{healthQuery.error.message}</Alert>
                ) : healthQuery.data ? (
                  <>
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                      <StatusChip value={healthQuery.data.health_status} />
                      <Typography variant="h2">{healthQuery.data.health_score}</Typography>
                    </Stack>
                    <Stack spacing={1}>
                      {healthQuery.data.signals.map((signal) => (
                        <Paper key={signal.code} sx={{ p: 1.5 }} variant="outlined">
                          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                            <StatusChip value={signal.severity} />
                            <Typography fontWeight={700}>{titleCase(signal.code)}</Typography>
                          </Stack>
                          <Typography color="text.secondary" sx={{ mt: 0.5 }} variant="body2">
                            {signal.message}
                          </Typography>
                        </Paper>
                      ))}
                    </Stack>
                  </>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Box>
      ) : null}

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h3">Events</Typography>
            {eventsQuery.isLoading ? (
              <CircularProgress size={28} />
            ) : eventsQuery.error ? (
              <Alert severity="warning">{eventsQuery.error.message}</Alert>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Reason</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Count</TableCell>
                    <TableCell>Last Seen</TableCell>
                    <TableCell>Message</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(eventsQuery.data ?? []).map((event, index) => (
                    <TableRow key={`${event.reason}-${index}`}>
                      <TableCell>{event.reason}</TableCell>
                      <TableCell>{event.event_type}</TableCell>
                      <TableCell>{event.count}</TableCell>
                      <TableCell>{formatDateTime(event.last_seen_at)}</TableCell>
                      <TableCell>{event.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Stack
              direction={{ xs: "column", md: "row" }}
              spacing={1.5}
              sx={{ justifyContent: "space-between" }}
            >
              <Typography variant="h3">Logs</Typography>
              <Stack direction="row" spacing={1}>
                <TextField
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchOutlinedIcon />
                      </InputAdornment>
                    ),
                  }}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search"
                  size="small"
                  value={search}
                />
                <TextField
                  onChange={(event) => setSeverity(event.target.value)}
                  select
                  size="small"
                  value={severity}
                >
                  {severityOptions.map((option) => (
                    <MenuItem key={option} value={option}>
                      {titleCase(option)}
                    </MenuItem>
                  ))}
                </TextField>
              </Stack>
            </Stack>
            {logsQuery.isLoading ? (
              <CircularProgress size={28} />
            ) : logsQuery.error ? (
              <Alert severity="warning">{logsQuery.error.message}</Alert>
            ) : (
              <Box
                component="pre"
                sx={{
                  bgcolor: "#111827",
                  borderRadius: 2,
                  color: "#d1fae5",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                  fontSize: 13,
                  lineHeight: 1.6,
                  m: 0,
                  maxHeight: 420,
                  overflow: "auto",
                  p: 2,
                  whiteSpace: "pre-wrap",
                }}
              >
                {filteredLogs.join("\n")}
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

function LoadingPanel() {
  return (
    <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
      <CircularProgress />
    </Box>
  );
}
