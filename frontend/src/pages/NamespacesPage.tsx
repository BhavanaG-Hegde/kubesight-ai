import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tabs,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getDeployments, getNamespaces, getPods, getServices } from "../api/kubernetes";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusChip } from "../components/StatusChip";
import type { DeploymentRead, PodRead, ServiceRead } from "../types/domain";

export function NamespacesPage() {
  const [namespace, setNamespace] = useState("");
  const [tab, setTab] = useState(0);

  const namespacesQuery = useQuery({
    queryKey: ["namespaces"],
    queryFn: getNamespaces,
  });

  const namespaces = useMemo(() => namespacesQuery.data ?? [], [namespacesQuery.data]);
  const selectedNamespace = namespace || namespaces[0]?.name || "";

  const podsQuery = useQuery({
    enabled: Boolean(selectedNamespace),
    queryKey: ["pods", selectedNamespace],
    queryFn: () => getPods(selectedNamespace),
  });
  const deploymentsQuery = useQuery({
    enabled: Boolean(selectedNamespace),
    queryKey: ["deployments", selectedNamespace],
    queryFn: () => getDeployments(selectedNamespace),
  });
  const servicesQuery = useQuery({
    enabled: Boolean(selectedNamespace),
    queryKey: ["services", selectedNamespace],
    queryFn: () => getServices(selectedNamespace),
  });

  const refresh = () => {
    void namespacesQuery.refetch();
    void podsQuery.refetch();
    void deploymentsQuery.refetch();
    void servicesQuery.refetch();
  };

  const namespaceOptions = useMemo(
    () => namespaces.map((item) => ({ label: item.name, value: item.name })),
    [namespaces],
  );

  return (
    <Stack spacing={3}>
      <PageHeader
        actions={
          <Stack direction="row" spacing={1}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="namespace-select-label">Namespace</InputLabel>
              <Select
                label="Namespace"
                labelId="namespace-select-label"
                onChange={(event) => setNamespace(event.target.value)}
                value={selectedNamespace}
              >
                {namespaceOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Tooltip title="Refresh">
              <IconButton aria-label="Refresh" onClick={refresh}>
                <RefreshOutlinedIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        }
        title="Namespace Explorer"
      />

      {namespacesQuery.isLoading ? (
        <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
          <CircularProgress />
        </Box>
      ) : namespacesQuery.error ? (
        <Alert severity="warning">{String(namespacesQuery.error.message)}</Alert>
      ) : namespaces.length === 0 ? (
        <EmptyState title="No namespaces found" />
      ) : (
        <Paper variant="outlined">
          <Tabs onChange={(_, value) => setTab(value)} value={tab}>
            <Tab label="Pods" />
            <Tab label="Deployments" />
            <Tab label="Services" />
          </Tabs>
          {tab === 0 ? (
            <PodsTable namespace={selectedNamespace} query={podsQuery} />
          ) : null}
          {tab === 1 ? <DeploymentsTable query={deploymentsQuery} /> : null}
          {tab === 2 ? <ServicesTable query={servicesQuery} /> : null}
        </Paper>
      )}
    </Stack>
  );
}

function PodsTable({
  namespace,
  query,
}: {
  namespace: string;
  query: UseQueryResult<PodRead[], Error>;
}) {
  if (query.isLoading) {
    return <LoadingPanel />;
  }
  if (query.error) {
    return <Alert severity="warning">{query.error.message}</Alert>;
  }
  const pods = query.data ?? [];
  if (pods.length === 0) {
    return <EmptyState title="No pods found" />;
  }
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>Phase</TableCell>
          <TableCell>Ready</TableCell>
          <TableCell>Restarts</TableCell>
          <TableCell>Node</TableCell>
          <TableCell align="right">Open</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {pods.map((pod) => (
          <TableRow hover key={pod.name}>
            <TableCell>
              <Typography fontWeight={700}>{pod.name}</Typography>
            </TableCell>
            <TableCell>
              <StatusChip value={pod.phase} />
            </TableCell>
            <TableCell>
              {pod.ready_containers}/{pod.total_containers}
            </TableCell>
            <TableCell>{pod.restart_count}</TableCell>
            <TableCell>{pod.node_name ?? "—"}</TableCell>
            <TableCell align="right">
              <Tooltip title="Open pod">
                <Button
                  component={Link}
                  endIcon={<OpenInNewOutlinedIcon />}
                  size="small"
                  to={`/namespaces/${namespace}/pods/${pod.name}`}
                >
                  Open
                </Button>
              </Tooltip>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function DeploymentsTable({
  query,
}: {
  query: UseQueryResult<DeploymentRead[], Error>;
}) {
  if (query.isLoading) {
    return <LoadingPanel />;
  }
  if (query.error) {
    return <Alert severity="warning">{query.error.message}</Alert>;
  }
  const deployments = query.data ?? [];
  if (deployments.length === 0) {
    return <EmptyState title="No deployments found" />;
  }
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>Desired</TableCell>
          <TableCell>Ready</TableCell>
          <TableCell>Available</TableCell>
          <TableCell>Updated</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {deployments.map((deployment) => (
          <TableRow hover key={deployment.name}>
            <TableCell>{deployment.name}</TableCell>
            <TableCell>{deployment.desired_replicas}</TableCell>
            <TableCell>{deployment.ready_replicas}</TableCell>
            <TableCell>{deployment.available_replicas}</TableCell>
            <TableCell>{deployment.updated_replicas}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function ServicesTable({
  query,
}: {
  query: UseQueryResult<ServiceRead[], Error>;
}) {
  if (query.isLoading) {
    return <LoadingPanel />;
  }
  if (query.error) {
    return <Alert severity="warning">{query.error.message}</Alert>;
  }
  const services = query.data ?? [];
  if (services.length === 0) {
    return <EmptyState title="No services found" />;
  }
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>Type</TableCell>
          <TableCell>Cluster IP</TableCell>
          <TableCell>Ports</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {services.map((service) => (
          <TableRow hover key={service.name}>
            <TableCell>{service.name}</TableCell>
            <TableCell>{service.service_type ?? "—"}</TableCell>
            <TableCell>{service.cluster_ip ?? "—"}</TableCell>
            <TableCell>
              {service.ports.map((port) => `${port.port}/${port.protocol}`).join(", ") || "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function LoadingPanel() {
  return (
    <Box sx={{ display: "grid", minHeight: 220, placeItems: "center" }}>
      <CircularProgress />
    </Box>
  );
}
