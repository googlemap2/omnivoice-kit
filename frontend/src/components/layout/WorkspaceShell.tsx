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
    <Box sx={{ p: { xs: 1.25, sm: 2 }, minWidth: 0 }}>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1.25}
        useFlexGap
        sx={{ mb: 2, flexWrap: "wrap" }}
      >
        {icon}
        <Typography variant="h1">{title}</Typography>
        <Box sx={{ flex: 1 }} />
        {action}
      </Stack>
      {children}
    </Box>
  );
}
