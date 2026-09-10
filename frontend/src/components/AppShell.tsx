import { useState, type ReactNode } from "react";
import { Link as RouterLink, useLocation } from "react-router-dom";
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import LightModeRoundedIcon from "@mui/icons-material/LightModeRounded";
import DarkModeRoundedIcon from "@mui/icons-material/DarkModeRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import { useThemeMode } from "../theme/ThemeModeContext";
import { useConfirm } from "./ConfirmDialogProvider";

const DRAWER_WIDTH = 252;

const NAV_ITEMS = [
  { label: "Agents", to: "/agents", match: "/agents", icon: SmartToyOutlinedIcon },
  { label: "Research", to: "/research", match: "/research", icon: TravelExploreOutlinedIcon },
];

interface AppShellProps {
  userName?: string;
  onLogout: () => void;
  children: ReactNode;
}

export function AppShell({ userName, onLogout, children }: AppShellProps) {
  const theme = useTheme();
  const location = useLocation();
  const { mode, toggleMode } = useThemeMode();
  const confirm = useConfirm();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);

  async function handleLogout() {
    setMenuAnchor(null);
    const ok = await confirm({
      title: "Log out?",
      description: "You'll need to sign in again to access your agents and research.",
      confirmText: "Log out",
      danger: true,
    });
    if (ok) onLogout();
  }

  const drawerContent = (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Toolbar sx={{ gap: 1.25, px: 2.5 }}>
        <HubRoundedIcon color="primary" fontSize="medium" />
        <Typography variant="subtitle1" noWrap sx={{ fontWeight: 700 }}>
          Research Assistant
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ px: 1.5, py: 2, flexGrow: 1 }}>
        {NAV_ITEMS.map(({ label, to, match, icon: Icon }) => {
          const selected = location.pathname.startsWith(match);
          return (
            <ListItemButton
              key={to}
              component={RouterLink}
              to={to}
              selected={selected}
              onClick={() => setMobileOpen(false)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                "&.Mui-selected": {
                  bgcolor: "primary.main",
                  color: "primary.contrastText",
                  "& .MuiListItemIcon-root": { color: "primary.contrastText" },
                  "&:hover": { bgcolor: "primary.dark" },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 38 }}>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                slotProps={{ primary: { sx: { fontWeight: 600, fontSize: "0.92rem" } } }}
              >
                {label}
              </ListItemText>
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          {!isDesktop && (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 0.5 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="subtitle1" sx={{ flexGrow: 1, fontWeight: 700 }} noWrap>
            {NAV_ITEMS.find((item) => location.pathname.startsWith(item.match))?.label ?? ""}
          </Typography>
          <Tooltip title={mode === "light" ? "Switch to dark mode" : "Switch to light mode"}>
            <IconButton onClick={toggleMode} color="inherit">
              {mode === "light" ? (
                <DarkModeRoundedIcon fontSize="small" />
              ) : (
                <LightModeRoundedIcon fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title="Account">
            <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)} sx={{ ml: 0.5 }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: "0.85rem" }}>
                {userName ? userName.slice(0, 1).toUpperCase() : <PersonRoundedIcon fontSize="small" />}
              </Avatar>
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={menuAnchor}
            open={menuAnchor != null}
            onClose={() => setMenuAnchor(null)}
            slotProps={{ paper: { sx: { minWidth: 200, mt: 1 } } }}
          >
            {userName && (
              <Stack sx={{ px: 2, py: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }} noWrap>
                  {userName}
                </Typography>
              </Stack>
            )}
            <Divider />
            <MenuItem onClick={handleLogout} sx={{ color: "error.main", gap: 1.25 }}>
              <LogoutRoundedIcon fontSize="small" />
              Log out
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ display: { xs: "block", md: "none" } }}
          slotProps={{ paper: { sx: { width: DRAWER_WIDTH } } }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{ display: { xs: "none", md: "block" } }}
          slotProps={{ paper: { sx: { width: DRAWER_WIDTH, border: "none" } } }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          minWidth: 0,
        }}
      >
        <Toolbar />
        <Box sx={{ p: { xs: 2, sm: 3, md: 4 } }}>{children}</Box>
      </Box>
    </Box>
  );
}
