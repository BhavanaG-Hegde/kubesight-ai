import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import AnalyticsOutlinedIcon from "@mui/icons-material/AnalyticsOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";
import LogoutOutlinedIcon from "@mui/icons-material/LogoutOutlined";
import ReportProblemOutlinedIcon from "@mui/icons-material/ReportProblemOutlined";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/useAuth";

const drawerWidth = 260;

const navItems = [
  { label: "Dashboard", path: "/dashboard", icon: <DashboardOutlinedIcon /> },
  { label: "Analytics", path: "/analytics", icon: <AnalyticsOutlinedIcon /> },
  { label: "Namespaces", path: "/namespaces", icon: <FolderOutlinedIcon /> },
  { label: "Incidents", path: "/incidents", icon: <ReportProblemOutlinedIcon /> },
  { label: "AI Assistant", path: "/ai", icon: <AutoAwesomeOutlinedIcon /> },
];

export function AppLayout() {
  const { logout, user } = useAuth();
  const location = useLocation();

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        color="inherit"
        elevation={0}
        position="fixed"
        sx={{
          borderBottom: "1px solid",
          borderColor: "divider",
          ml: { md: `${drawerWidth}px` },
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Typography variant="h3">KubeSight AI</Typography>
          <Box sx={{ alignItems: "center", display: "flex", gap: 1.5 }}>
            <Typography color="text.secondary" variant="body2">
              {user?.full_name}
            </Typography>
            <Tooltip title="Log out">
              <IconButton aria-label="Log out" onClick={logout}>
                <LogoutOutlinedIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        open
        variant="permanent"
        sx={{
          display: { xs: "none", md: "block" },
          width: drawerWidth,
          "& .MuiDrawer-paper": {
            borderRight: "1px solid",
            borderColor: "divider",
            width: drawerWidth,
          },
        }}
      >
        <Toolbar>
          <Typography sx={{ fontWeight: 800 }} variant="h3">
            KubeSight AI
          </Typography>
        </Toolbar>
        <Divider />
        <List sx={{ p: 1.5 }}>
          {navItems.map((item) => {
            const selected = location.pathname.startsWith(item.path);
            return (
              <ListItemButton
                component={NavLink}
                key={item.path}
                selected={selected}
                sx={{ borderRadius: 1, mb: 0.5 }}
                to={item.path}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            );
          })}
        </List>
      </Drawer>

      <Box sx={{ display: { xs: "block", md: "none" }, position: "fixed", bottom: 16, left: 16, zIndex: 20 }}>
        {navItems.map((item) => (
          <Button
            component={NavLink}
            key={item.path}
            size="small"
            sx={{ mr: 0.75 }}
            to={item.path}
            variant={location.pathname.startsWith(item.path) ? "contained" : "outlined"}
          >
            {item.label}
          </Button>
        ))}
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          px: { xs: 2, md: 4 },
          py: 4,
          pt: 11,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
