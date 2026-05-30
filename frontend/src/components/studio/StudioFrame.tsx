"use client";

import { Box } from "@mui/material";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { ActivityBar } from "../layout/ActivityBar";
import { Editor } from "../layout/Editor";
import { Explorer } from "../layout/Explorer";
import { TitleBar } from "../layout/TitleBar";
import type { Workspace } from "../../types/studio";
import { useStudio } from "./StudioContext";

export function StudioFrame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const workspace = workspaceFromPath(pathname);
  const studio = useStudio();
  const [explorerCollapsed, setExplorerCollapsed] = useState(false);

  return (
    <Box sx={{ height: "100vh", display: "grid", gridTemplateRows: "34px 1fr" }}>
      <TitleBar busy={studio.busy} onRefresh={studio.refreshAll} />
      <Box
        sx={{
          minHeight: 0,
          display: "grid",
          gridTemplateColumns: `48px ${explorerCollapsed ? "44px" : "280px"} 1fr`,
          transition: "grid-template-columns 160ms ease",
        }}
      >
        <ActivityBar workspace={workspace} />
        <Explorer
          workspace={workspace}
          collapsed={explorerCollapsed}
          onToggleCollapsed={() => setExplorerCollapsed((current) => !current)}
        />
        <Editor>{children}</Editor>
      </Box>
    </Box>
  );
}

function workspaceFromPath(pathname: string): Workspace {
  if (pathname.startsWith("/transcription")) return "transcribe";
  if (pathname.startsWith("/translation")) return "translate";
  if (pathname.startsWith("/dubbing")) return "dubbing";
  if (pathname.startsWith("/jobs")) return "jobs";
  if (pathname.startsWith("/voices")) return "voices";
  if (pathname.startsWith("/settings")) return "settings";
  return "tts";
}
