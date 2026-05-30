"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LibraryMusicIcon from "@mui/icons-material/LibraryMusic";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";

export default function VoicesPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<LibraryMusicIcon />}
      title="Voice Profiles"
      action={
        <Button startIcon={<AutoAwesomeIcon />} variant="contained" onClick={studio.createVoice}>
          Create Voice
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "360px 1fr" }, gap: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Speaker ID"
            value={studio.newVoiceId}
            onChange={(event) => studio.setNewVoiceId(event.target.value)}
          />
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {studio.newVoiceFile ? studio.newVoiceFile.name : "Choose reference audio"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => studio.setNewVoiceFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField label="Language" value={studio.language} onChange={studio.setLanguage} options={studio.meta.languages} />
          <TextField
            label="Reference transcript"
            multiline
            minRows={6}
            value={studio.newVoiceText}
            onChange={(event) => studio.setNewVoiceText(event.target.value)}
          />
        </Stack>
        <Stack spacing={1}>
          {studio.voices.map((voice) => (
            <Paper key={voice.id} variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
              <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={2}>
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 600 }}>{voice.name || voice.id}</Typography>
                  <Typography sx={{ fontSize: 12, color: "text.secondary", overflowWrap: "anywhere" }}>{voice.prompt_path}</Typography>
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
