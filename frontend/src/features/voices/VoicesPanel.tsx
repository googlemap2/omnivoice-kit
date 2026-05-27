import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LibraryMusicIcon from "@mui/icons-material/LibraryMusic";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { WorkspaceShell } from "../../components/layout/WorkspaceShell";
import { SelectField } from "../../components/ui/SelectField";
import type { Meta, Voice } from "../../types/api";

type VoicesPanelProps = {
  voices: Voice[];
  language: string;
  setLanguage: (language: string) => void;
  meta: Meta;
  newVoiceId: string;
  setNewVoiceId: (id: string) => void;
  newVoiceText: string;
  setNewVoiceText: (text: string) => void;
  newVoiceFile: File | null;
  setNewVoiceFile: (file: File | null) => void;
  onCreate: () => void;
};

export function VoicesPanel(props: VoicesPanelProps) {
  return (
    <WorkspaceShell
      icon={<LibraryMusicIcon />}
      title="Voice Profiles"
      action={
        <Button startIcon={<AutoAwesomeIcon />} variant="contained" onClick={props.onCreate}>
          Create Voice
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Speaker ID"
            value={props.newVoiceId}
            onChange={(event) => props.setNewVoiceId(event.target.value)}
          />
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {props.newVoiceFile ? props.newVoiceFile.name : "Choose reference audio"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => props.setNewVoiceFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField label="Language" value={props.language} onChange={props.setLanguage} options={props.meta.languages} />
          <TextField
            label="Reference transcript"
            multiline
            minRows={6}
            value={props.newVoiceText}
            onChange={(event) => props.setNewVoiceText(event.target.value)}
          />
        </Stack>
        <Stack spacing={1}>
          {props.voices.map((voice) => (
            <Paper key={voice.id} variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
              <Stack direction="row" justifyContent="space-between" spacing={2}>
                <Box>
                  <Typography sx={{ fontWeight: 600 }}>{voice.name || voice.id}</Typography>
                  <Typography sx={{ fontSize: 12, color: "text.secondary" }}>{voice.prompt_path}</Typography>
                </Box>
                <Chip size="small" label={voice.language || "auto"} />
              </Stack>
            </Paper>
          ))}
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
