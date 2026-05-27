"use client";

import { Box } from "@mui/material";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
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

  return (
    <Box sx={{ height: "100vh", display: "grid", gridTemplateRows: "34px 1fr" }}>
      <TitleBar busy={studio.busy} onRefresh={studio.refreshAll} />
      <Box sx={{ minHeight: 0, display: "grid", gridTemplateColumns: "48px 280px 1fr" }}>
        <ActivityBar workspace={workspace} />
        <Explorer
          workspace={workspace}
          voices={studio.voices}
          selectedVoice={studio.selectedVoice}
          setSelectedVoice={studio.setSelectedVoice}
        />
        <Editor>{children}</Editor>
      </Box>
    </Box>
  );
}

function workspaceFromPath(pathname: string): Workspace {
  if (pathname.startsWith("/transcription")) return "transcribe";
  if (pathname.startsWith("/translation")) return "translate";
  if (pathname.startsWith("/voices")) return "voices";
  if (pathname.startsWith("/settings")) return "settings";
  return "tts";
}
