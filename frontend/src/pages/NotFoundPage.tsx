import { Box, Button, Stack, Typography } from "@mui/material";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <Box sx={{ display: "grid", minHeight: "100vh", placeItems: "center", p: 3 }}>
      <Stack spacing={2} sx={{ alignItems: "center" }}>
        <Typography variant="h1">Not Found</Typography>
        <Button component={Link} to="/dashboard" variant="contained">
          Dashboard
        </Button>
      </Stack>
    </Box>
  );
}
