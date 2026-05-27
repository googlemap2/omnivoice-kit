"use client";

import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SubtitlesIcon from "@mui/icons-material/Subtitles";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Stack, TextField } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";

export default function TranscriptionPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<SubtitlesIcon />}
      title="Transcription"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={studio.transcribe}>
          Run ASR
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {studio.transcribeFile ? studio.transcribeFile.name : "Choose media file"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => studio.setTranscribeFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField
            label="ASR model"
            value={studio.asrModel}
            onChange={studio.setAsrModel}
            options={studio.meta.asr_models}
          />
          <SelectField label="Language" value={studio.language} onChange={studio.setLanguage} options={studio.meta.languages} />
          <SelectField
            label="Output"
            value={studio.transcribeFormat}
            onChange={studio.setTranscribeFormat}
            options={studio.meta.transcription_formats.map((id) => ({ id, label: id }))}
          />
        </Stack>
        <TextField
          label="Transcript output"
          multiline
          minRows={18}
          value={studio.transcription}
          InputProps={{ readOnly: true }}
        />
      </Box>
    </WorkspaceShell>
  );
}
