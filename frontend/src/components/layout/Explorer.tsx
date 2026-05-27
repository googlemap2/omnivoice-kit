import { Box, Chip, Divider, List, ListItemButton, ListItemText, Stack, Typography } from "@mui/material";
import type { ModelStatus, TranslationProvider, Voice } from "../../types/api";
import type { Workspace } from "../../types/studio";
import { SectionTitle } from "../ui/SectionTitle";

type ExplorerProps = {
  workspace: Workspace;
  voices: Voice[];
  statuses: ModelStatus[];
  providers: TranslationProvider[];
  selectedVoice: string;
  setSelectedVoice: (voice: string) => void;
  installedCount: number;
};

export function Explorer({
  workspace,
  voices,
  statuses,
  providers,
  selectedVoice,
  setSelectedVoice,
  installedCount,
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
      <Divider sx={{ my: 1 }} />
      <SectionTitle title="Models" />
      <Stack sx={{ px: 2, py: 0.5 }} spacing={0.75}>
        <Chip size="small" label={`${installedCount}/${statuses.length || 0} installed`} />
        {statuses.map((status) => (
          <Chip
            key={status.repo_id}
            size="small"
            color={status.installed ? "success" : "warning"}
            variant="outlined"
            label={status.repo_id}
          />
        ))}
      </Stack>
      <Divider sx={{ my: 1 }} />
      <SectionTitle title="Translation Providers" />
      <Stack sx={{ px: 2 }} spacing={0.75}>
        {providers.map((item) => (
          <Chip
            key={item.id}
            size="small"
            color={item.available ? "success" : "default"}
            variant="outlined"
            label={item.id}
          />
        ))}
      </Stack>
    </Box>
  );
}

function workspaceLabel(workspace: Workspace) {
  return {
    tts: "Speech",
    transcribe: "Transcription",
    translate: "Translation",
    voices: "Voices",
    settings: "Settings",
  }[workspace];
}
