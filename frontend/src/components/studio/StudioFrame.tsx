"use client";

import { Box } from "@mui/material";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ActivityBar } from "../layout/ActivityBar";
import { Editor } from "../layout/Editor";
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
      <Box
        sx={{
          minHeight: 0,
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "48px 1fr" },
          gridTemplateRows: { xs: "1fr 56px", md: "1fr" },
          gridTemplateAreas: {
            xs: '"editor" "activity"',
            md: '"activity editor"',
          },
        }}
      >
        <Box sx={{ gridArea: "activity", minWidth: 0, minHeight: 0 }}>
          <ActivityBar workspace={workspace} />
        </Box>
        <Box sx={{ gridArea: "editor", minWidth: 0, minHeight: 0 }}>
          <Editor>{children}</Editor>
        </Box>
      </Box>
    </Box>
  );
}

function workspaceFromPath(pathname: string): Workspace {
  if (pathname.startsWith("/transcription")) return "transcribe";
  if (pathname.startsWith("/translation")) return "translate";
  if (pathname.startsWith("/provider-chat")) return "provider-chat";
  if (pathname.startsWith("/dubbing")) return "dubbing";
  if (pathname.startsWith("/jobs")) return "jobs";
  if (pathname.startsWith("/voices")) return "voices";
  if (pathname.startsWith("/settings")) return "settings";
  return "tts";
}
