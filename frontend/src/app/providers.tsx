"use client";

import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import type { ReactNode } from "react";

const theme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#1e1e1e",
      paper: "#252526",
    },
    primary: {
      main: "#4ea1ff",
    },
    secondary: {
      main: "#d7ba7d",
    },
    success: {
      main: "#89d185",
    },
    warning: {
      main: "#cca700",
    },
    error: {
      main: "#f48771",
    },
    text: {
      primary: "#cccccc",
      secondary: "#9d9d9d",
    },
    divider: "#3c3c3c",
  },
  shape: {
    borderRadius: 4,
  },
  typography: {
    fontFamily:
      '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif',
    h1: { fontSize: "1.4rem", fontWeight: 600 },
    h2: { fontSize: "1.05rem", fontWeight: 600 },
    h3: { fontSize: "0.92rem", fontWeight: 600 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 32,
          boxShadow: "none",
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        size: "small",
      },
    },
    MuiSelect: {
      defaultProps: {
        size: "small",
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: "#1f1f1f",
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        outlined: {
          backgroundColor: "#1f1f1f",
          paddingLeft: 4,
          paddingRight: 4,
        },
      },
    },
    MuiTooltip: {
      defaultProps: {
        arrow: true,
      },
    },
  },
});

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AppRouterCacheProvider options={{ enableCssLayer: true }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AppRouterCacheProvider>
  );
}
