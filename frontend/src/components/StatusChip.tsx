import { Chip } from "@mui/material";

import type { HealthStatus, IncidentSeverity, IncidentStatus } from "../types/domain";
import { titleCase } from "../utils/format";

type StatusChipProps = {
  value: HealthStatus | IncidentSeverity | IncidentStatus | string;
};

export function StatusChip({ value }: StatusChipProps) {
  const color = chipColor(value);
  return <Chip color={color} label={titleCase(value)} size="small" variant="outlined" />;
}

function chipColor(value: string): "default" | "success" | "warning" | "error" | "info" {
  if (["healthy", "resolved", "running", "info"].includes(value.toLowerCase())) {
    return "success";
  }
  if (["warning", "pending", "acknowledged"].includes(value.toLowerCase())) {
    return "warning";
  }
  if (["critical", "failed", "open"].includes(value.toLowerCase())) {
    return "error";
  }
  return "default";
}
