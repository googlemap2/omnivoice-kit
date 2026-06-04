import GraphicEqIcon from "@mui/icons-material/GraphicEq";
import LibraryMusicIcon from "@mui/icons-material/LibraryMusic";
import MovieIcon from "@mui/icons-material/Movie";
import QueueIcon from "@mui/icons-material/Queue";
import SettingsIcon from "@mui/icons-material/Settings";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SubtitlesIcon from "@mui/icons-material/Subtitles";
import TranslateIcon from "@mui/icons-material/Translate";
import { Box, IconButton, Stack, Tooltip } from "@mui/material";
import Link from "next/link";
import type { ReactNode } from "react";
import type { Workspace } from "../../types/studio";

type ActivityBarProps = {
  workspace: Workspace;
};

export function ActivityBar({ workspace }: ActivityBarProps) {
  const items: Array<[Workspace, string, ReactNode, string]> = [
    ["tts", "/speech", <GraphicEqIcon key="tts" />, "Speech"],
    ["transcribe", "/transcription", <SubtitlesIcon key="transcribe" />, "Transcription"],
    ["translate", "/translation", <TranslateIcon key="translate" />, "Translation"],
    ["provider-chat", "/provider-chat", <SmartToyIcon key="provider-chat" />, "Provider Chat"],
    ["dubbing", "/dubbing", <MovieIcon key="dubbing" />, "Dubbing"],
    ["jobs", "/jobs", <QueueIcon key="jobs" />, "Jobs"],
    ["voices", "/voices", <LibraryMusicIcon key="voices" />, "Voices"],
    ["settings", "/settings", <SettingsIcon key="settings" />, "Settings"],
  ];

  return (
    <Box
      sx={{
        bgcolor: "#333333",
        borderColor: "divider",
        borderRight: { xs: 0, md: "1px solid" },
        borderTop: { xs: "1px solid", md: 0 },
        height: "100%",
        px: { xs: 0.5, md: 0 },
        py: { xs: 0, md: 0.5 },
      }}
    >
      <Stack
        direction={{ xs: "row", md: "column" }}
        alignItems="center"
        justifyContent={{ xs: "space-around", md: "flex-start" }}
        spacing={{ xs: 0, md: 0.5 }}
        sx={{ height: "100%", overflowX: "auto" }}
      >
        {items.map(([id, href, icon, label]) => (
          <Tooltip key={id} title={label} placement="right">
            <IconButton
              component={Link}
              href={href}
              sx={{
                width: 42,
                height: 42,
                color: workspace === id ? "#ffffff" : "text.secondary",
                borderLeft: { xs: 0, md: workspace === id ? "2px solid #ffffff" : "2px solid transparent" },
                borderBottom: { xs: workspace === id ? "2px solid #ffffff" : "2px solid transparent", md: 0 },
                borderRadius: 0,
              }}
            >
              {icon}
            </IconButton>
          </Tooltip>
        ))}
      </Stack>
    </Box>
  );
}
