import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { analyzeIncident } from "../api/ai";
import { getIncidents, syncNamespaceIncidents, updateIncidentStatus } from "../api/incidents";
import { PageHeader } from "../components/PageHeader";
import { StatusChip } from "../components/StatusChip";
import type { IncidentStatus } from "../types/domain";
import { formatDateTime, titleCase } from "../utils/format";

const statusOptions = ["", "open", "acknowledged", "resolved"];
const severityOptions = ["", "info", "warning", "critical"];

export function IncidentsPage() {
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [search, setSearch] = useState("");
  const [namespace, setNamespace] = useState("");
  const [analysis, setAnalysis] = useState("");
  const queryClient = useQueryClient();

  const incidentsQuery = useQuery({
    queryKey: ["incidents", status, severity, search],
    queryFn: () => getIncidents({ status, severity, search }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, nextStatus }: { id: string; nextStatus: IncidentStatus }) =>
      updateIncidentStatus(id, nextStatus),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incidents"] }),
  });

  const syncMutation = useMutation({
    mutationFn: syncNamespaceIncidents,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incidents"] }),
  });

  const analyzeMutation = useMutation({
    mutationFn: analyzeIncident,
    onSuccess: (result) => setAnalysis(result.response),
  });

  const incidents = incidentsQuery.data?.items ?? [];

  return (
    <Stack spacing={3}>
      <PageHeader
        actions={
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
            <TextField
              label="Namespace"
              onChange={(event) => setNamespace(event.target.value)}
              size="small"
              value={namespace}
            />
            <Button
              disabled={!namespace || syncMutation.isPending}
              onClick={() => syncMutation.mutate(namespace)}
              startIcon={<RefreshOutlinedIcon />}
              variant="contained"
            >
              Sync
            </Button>
          </Stack>
        }
        title="Incident History"
      />

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={1.5}>
              <TextField
                label="Search"
                onChange={(event) => setSearch(event.target.value)}
                size="small"
                value={search}
              />
              <TextField
                label="Status"
                onChange={(event) => setStatus(event.target.value)}
                select
                size="small"
                sx={{ minWidth: 160 }}
                value={status}
              >
                {statusOptions.map((option) => (
                  <MenuItem key={option || "all"} value={option}>
                    {option ? titleCase(option) : "All"}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Severity"
                onChange={(event) => setSeverity(event.target.value)}
                select
                size="small"
                sx={{ minWidth: 160 }}
                value={severity}
              >
                {severityOptions.map((option) => (
                  <MenuItem key={option || "all"} value={option}>
                    {option ? titleCase(option) : "All"}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>

            {incidentsQuery.isLoading ? (
              <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
                <CircularProgress />
              </Box>
            ) : incidentsQuery.error ? (
              <Alert severity="warning">{incidentsQuery.error.message}</Alert>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Incident</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Namespace</TableCell>
                    <TableCell>Pod</TableCell>
                    <TableCell>Last Seen</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {incidents.map((incident) => (
                    <TableRow hover key={incident.id}>
                      <TableCell>
                        <Typography fontWeight={700}>{incident.title}</Typography>
                        <Typography color="text.secondary" variant="caption">
                          {titleCase(incident.incident_type)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <StatusChip value={incident.severity} />
                      </TableCell>
                      <TableCell>
                        <StatusChip value={incident.status} />
                      </TableCell>
                      <TableCell>{incident.namespace ?? "—"}</TableCell>
                      <TableCell>{incident.pod_name ?? "—"}</TableCell>
                      <TableCell>{formatDateTime(incident.last_seen_at)}</TableCell>
                      <TableCell align="right">
                        <Tooltip title="Analyze">
                          <IconButton
                            aria-label="Analyze incident"
                            onClick={() => analyzeMutation.mutate(incident.id)}
                          >
                            <SmartToyOutlinedIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Resolve">
                          <IconButton
                            aria-label="Resolve incident"
                            disabled={incident.status === "resolved"}
                            onClick={() =>
                              updateStatusMutation.mutate({
                                id: incident.id,
                                nextStatus: "resolved",
                              })
                            }
                          >
                            <CheckCircleOutlineOutlinedIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Stack>
        </CardContent>
      </Card>

      {analysis ? (
        <Card variant="outlined">
          <CardContent>
            <Typography gutterBottom variant="h3">
              AI Analysis
            </Typography>
            <Typography sx={{ whiteSpace: "pre-wrap" }}>{analysis}</Typography>
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  );
}
