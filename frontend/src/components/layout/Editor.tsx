import { Box } from "@mui/material";
import type { ReactNode } from "react";

export function Editor({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ minWidth: 0, minHeight: 0, height: "100%", overflow: "auto", bgcolor: "#1e1e1e" }}>
      {children}
    </Box>
  );
}
