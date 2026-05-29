import { Box, Divider, List, ListItemButton, ListItemText, Typography } from "@mui/material";
import type { Voice } from "../../types/api";
import type { Workspace } from "../../types/studio";
import { SectionTitle } from "../ui/SectionTitle";

type ExplorerProps = {
  workspace: Workspace;
  voices: Voice[];
  selectedVoice: string;
  setSelectedVoice: (voice: string) => void;
};

export function Explorer({
  workspace,
  voices,
  selectedVoice,
  setSelectedVoice,
}: ExplorerProps) {
  return (
    <Box sx={{ bgcolor: "#252526", borderRight: "1px solid", borderColor: "divider", minHeight: 0 }}>
      <Box sx={{ px: 2, py: 1.25 }}>
        <Typography sx={{ fontSize: 11, textTransform: "uppercase", color: "text.secondary" }}>
          Explorer
        </Typography>
        <Typography variant="h2" sx={{ mt: 0.5 }}>
          {workspaceLabel(workspace)}
        </Typography>
      </Box>
      {workspace === "tts" && (
        <>
          <Divider />
          <SectionTitle title="Voices" />
          <List dense disablePadding>
            {voices.map((voice) => (
              <ListItemButton
                key={voice.id}
                selected={selectedVoice === voice.id}
                onClick={() => setSelectedVoice(voice.id)}
              >
                <ListItemText
                  primary={voice.name || voice.id}
                  secondary={`${voice.language || "auto"} - ${voice.type}`}
                  primaryTypographyProps={{ fontSize: 13 }}
                  secondaryTypographyProps={{ fontSize: 11 }}
                />
              </ListItemButton>
            ))}
            {voices.length === 0 && (
              <Typography sx={{ px: 2, py: 1, fontSize: 12, color: "text.secondary" }}>
                No voice profiles found.
              </Typography>
            )}
          </List>
        </>
      )}
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
