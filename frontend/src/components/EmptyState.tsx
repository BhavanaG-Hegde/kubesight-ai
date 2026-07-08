import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  icon?: ReactNode;
}

export function EmptyState({ title, icon }: EmptyStateProps) {
  return (
    <Box
      sx={{
        alignItems: "center",
        border: "1px dashed",
        borderColor: "divider",
        borderRadius: 2,
        display: "flex",
        flexDirection: "column",
        gap: 1,
        minHeight: 180,
        justifyContent: "center",
        p: 3,
      }}
    >
      {icon}
      <Typography color="text.secondary">{title}</Typography>
    </Box>
  );
}
