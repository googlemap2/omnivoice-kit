import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { Box, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import type { Workspace } from "../../types/studio";

type ExplorerProps = {
  workspace: Workspace;
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

export function Explorer({ workspace, collapsed, onToggleCollapsed }: ExplorerProps) {
  return (
    <Box sx={{ bgcolor: "#252526", borderRight: "1px solid", borderColor: "divider", minHeight: 0, overflow: "hidden" }}>
      <Box sx={{ px: collapsed ? 0.5 : 2, py: 1.25 }}>
        {collapsed ? (
          <Tooltip title="Expand Explorer" placement="right">
            <IconButton size="small" onClick={onToggleCollapsed} sx={{ width: 32, height: 32 }}>
              <ChevronRightIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ) : (
          <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent="space-between">
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: 11, textTransform: "uppercase", color: "text.secondary" }}>
                Explorer
              </Typography>
              <Typography variant="h2" sx={{ mt: 0.5 }}>
                {workspaceLabel(workspace)}
              </Typography>
            </Box>
            <Tooltip title="Collapse Explorer" placement="left">
              <IconButton size="small" onClick={onToggleCollapsed} sx={{ mt: -0.25 }}>
                <ChevronLeftIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        )}
      </Box>
    </Box>
  );
}

function workspaceLabel(workspace: Workspace) {
  return {
    tts: "Speech",
    transcribe: "Transcription",
    translate: "Translation",
    dubbing: "Dubbing",
    jobs: "Jobs",
    voices: "Voices",
    settings: "Settings",
  }[workspace];
}
