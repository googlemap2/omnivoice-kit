import { Box, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

type WorkspaceShellProps = {
  icon: ReactNode;
  title: string;
  action?: ReactNode;
  children: ReactNode;
};

export function WorkspaceShell({ icon, title, action, children }: WorkspaceShellProps) {
  return (
    <Box sx={{ p: 2, minWidth: 860 }}>
      <Stack direction="row" alignItems="center" spacing={1.25} sx={{ mb: 2 }}>
        {icon}
        <Typography variant="h1">{title}</Typography>
        <Box sx={{ flex: 1 }} />
        {action}
      </Stack>
      {children}
    </Box>
  );
}
