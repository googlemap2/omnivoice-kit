import GraphicEqIcon from "@mui/icons-material/GraphicEq";
import LibraryMusicIcon from "@mui/icons-material/LibraryMusic";
import MovieIcon from "@mui/icons-material/Movie";
import SettingsIcon from "@mui/icons-material/Settings";
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
    ["dubbing", "/dubbing", <MovieIcon key="dubbing" />, "Dubbing"],
    ["voices", "/voices", <LibraryMusicIcon key="voices" />, "Voices"],
    ["settings", "/settings", <SettingsIcon key="settings" />, "Settings"],
  ];

  return (
    <Box sx={{ bgcolor: "#333333", borderRight: "1px solid", borderColor: "divider", py: 0.5 }}>
      <Stack alignItems="center" spacing={0.5}>
        {items.map(([id, href, icon, label]) => (
          <Tooltip key={id} title={label} placement="right">
            <IconButton
              component={Link}
              href={href}
              sx={{
                width: 42,
                height: 42,
                color: workspace === id ? "#ffffff" : "text.secondary",
                borderLeft: workspace === id ? "2px solid #ffffff" : "2px solid transparent",
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
