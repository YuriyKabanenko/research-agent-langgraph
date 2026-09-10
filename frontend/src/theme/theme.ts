import { alpha, createTheme, type PaletteMode } from "@mui/material/styles";

// Shared design tokens (radius, spacing, typography) stay identical across modes -
// only palette values differ. Keeping this in one factory (rather than two static
// themes) means a token change never accidentally drifts between light and dark.
const SHAPE_RADIUS = 12;

const FONT_STACK =
  '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

interface Tokens {
  primaryMain: string;
  primaryLight: string;
  primaryDark: string;
  primaryContrast: string;
  secondaryMain: string;
  secondaryLight: string;
  secondaryDark: string;
  secondaryContrast: string;
  bgDefault: string;
  bgPaper: string;
  textPrimary: string;
  textSecondary: string;
  divider: string;
}

const LIGHT: Tokens = {
  primaryMain: "#4f46e5",
  primaryLight: "#818cf8",
  primaryDark: "#3730a3",
  primaryContrast: "#ffffff",
  secondaryMain: "#0d9488",
  secondaryLight: "#5eead4",
  secondaryDark: "#0f766e",
  secondaryContrast: "#ffffff",
  bgDefault: "#f4f5fa",
  bgPaper: "#ffffff",
  textPrimary: "#111827",
  textSecondary: "#5b6472",
  divider: "rgba(17, 24, 39, 0.09)",
};

const DARK: Tokens = {
  primaryMain: "#818cf8",
  primaryLight: "#a5b4fc",
  primaryDark: "#6366f1",
  primaryContrast: "#0b0d14",
  secondaryMain: "#2dd4bf",
  secondaryLight: "#5eead4",
  secondaryDark: "#14b8a6",
  secondaryContrast: "#0b0d14",
  bgDefault: "#0b0d14",
  bgPaper: "#141722",
  textPrimary: "#f3f4f6",
  textSecondary: "#9aa2b1",
  divider: "rgba(255, 255, 255, 0.09)",
};

export function getTheme(mode: PaletteMode) {
  const t = mode === "light" ? LIGHT : DARK;

  return createTheme({
    palette: {
      mode,
      primary: { main: t.primaryMain, light: t.primaryLight, dark: t.primaryDark, contrastText: t.primaryContrast },
      secondary: {
        main: t.secondaryMain,
        light: t.secondaryLight,
        dark: t.secondaryDark,
        contrastText: t.secondaryContrast,
      },
      error: { main: mode === "light" ? "#dc2626" : "#f87171" },
      warning: { main: mode === "light" ? "#d97706" : "#fbbf24" },
      success: { main: mode === "light" ? "#16a34a" : "#4ade80" },
      info: { main: mode === "light" ? "#0284c7" : "#38bdf8" },
      background: { default: t.bgDefault, paper: t.bgPaper },
      text: { primary: t.textPrimary, secondary: t.textSecondary },
      divider: t.divider,
    },
    shape: { borderRadius: SHAPE_RADIUS },
    typography: {
      fontFamily: FONT_STACK,
      h4: { fontWeight: 700, letterSpacing: -0.5 },
      h5: { fontWeight: 700, letterSpacing: -0.3 },
      h6: { fontWeight: 600 },
      subtitle1: { fontWeight: 600 },
      button: { fontWeight: 600, textTransform: "none" },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundImage:
              mode === "light"
                ? "radial-gradient(1200px circle at 100% -10%, rgba(79,70,229,0.07), transparent 45%), radial-gradient(1000px circle at -10% 20%, rgba(13,148,136,0.06), transparent 40%)"
                : "radial-gradient(1200px circle at 100% -10%, rgba(129,140,248,0.10), transparent 45%), radial-gradient(1000px circle at -10% 20%, rgba(45,212,191,0.07), transparent 40%)",
            backgroundAttachment: "fixed",
          },
          "*": { scrollbarWidth: "thin" },
          "*::-webkit-scrollbar": { width: 8, height: 8 },
          "*::-webkit-scrollbar-thumb": {
            backgroundColor: alpha(t.textPrimary, 0.18),
            borderRadius: 8,
          },
          "*::-webkit-scrollbar-track": { backgroundColor: "transparent" },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: "none" },
          outlined: { borderColor: t.divider },
        },
        defaultProps: { elevation: 0 },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            border: `1px solid ${t.divider}`,
            borderRadius: SHAPE_RADIUS + 4,
            boxShadow: "none",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: alpha(t.bgPaper, 0.8),
            backdropFilter: "blur(12px)",
            color: t.textPrimary,
            borderBottom: `1px solid ${t.divider}`,
          },
        },
        defaultProps: { elevation: 0 },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: t.bgPaper,
            backgroundImage: "none",
            borderRight: `1px solid ${t.divider}`,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: SHAPE_RADIUS - 2,
            paddingInline: 18,
            paddingBlock: 9,
          },
          contained: {
            boxShadow: "none",
            "&:hover": { boxShadow: "none" },
          },
          sizeSmall: { paddingInline: 12, paddingBlock: 5 },
        },
      },
      MuiIconButton: {
        styleOverrides: { root: { borderRadius: SHAPE_RADIUS - 4 } },
      },
      MuiTextField: {
        defaultProps: { variant: "outlined" },
      },
      MuiInputLabel: {
        styleOverrides: {
          root: {
            fontWeight: 500,
            color: t.textSecondary,
            "&.Mui-focused": { color: t.primaryMain },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: SHAPE_RADIUS - 2,
            backgroundColor: mode === "light" ? alpha("#111827", 0.02) : alpha("#ffffff", 0.03),
          },
          notchedOutline: { borderColor: t.divider },
        },
      },
      MuiFormHelperText: {
        styleOverrides: { root: { marginLeft: 2 } },
      },
      MuiChip: {
        styleOverrides: {
          root: { fontWeight: 600, borderRadius: 8 },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: { borderColor: t.divider },
          head: {
            fontWeight: 700,
            fontSize: "0.72rem",
            letterSpacing: 0.4,
            textTransform: "uppercase",
            color: t.textSecondary,
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            "&:last-of-type td": { borderBottom: "none" },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: { borderRadius: SHAPE_RADIUS + 4 },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: { borderRadius: SHAPE_RADIUS - 2 },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: { fontSize: "0.72rem", fontWeight: 500 },
        },
      },
    },
  });
}
