"use client";

import MovieIcon from "@mui/icons-material/Movie";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Chip, FormControlLabel, Paper, Stack, Switch, TextField, Typography } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { useStudio } from "../../../components/studio/StudioContext";
import { SelectField } from "../../../components/ui/SelectField";

export default function DubbingPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<MovieIcon />}
      title="Dubbing"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={studio.runDubbing}>
          Dub Media
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "360px minmax(0, 1fr)", gap: 2 }}>
        <Stack spacing={2}>
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {studio.dubbingFile ? studio.dubbingFile.name : "Choose audio or video"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => studio.setDubbingFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField
            label="Voice"
            value={studio.dubbingVoice}
            onChange={studio.setDubbingVoice}
            options={studio.voices.map((voice) => ({ id: voice.id, label: voice.name || voice.id }))}
          />
          <SelectField
            label="Source language"
            value={studio.dubbingSourceLanguage}
            onChange={studio.setDubbingSourceLanguage}
            options={studio.meta.translation_languages}
          />
          <SelectField
            label="Target language"
            value={studio.dubbingTargetLanguage}
            onChange={studio.setDubbingTargetLanguage}
            options={studio.meta.translation_languages.filter((item) => item.id)}
          />
          <SelectField
            label="Translation provider"
            value={studio.dubbingProvider}
            onChange={studio.setDubbingProvider}
            options={studio.providers.map((provider) => ({ id: provider.id, label: provider.name }))}
          />
          <SelectField
            label="ASR model"
            value={studio.asrModel}
            onChange={studio.setAsrModel}
            options={studio.meta.asr_models}
          />
          <SelectField
            label="Effect"
            value={studio.effectPreset}
            onChange={(value) => studio.setEffectPreset(value as "raw" | "normalize" | "broadcast")}
            options={studio.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <FormControlLabel
            control={
              <Switch
                checked={studio.dubbingDiarize}
                onChange={(event) => studio.setDubbingDiarize(event.target.checked)}
              />
            }
            label="Diarize speakers"
          />
        </Stack>

        <Stack spacing={2}>
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
            <Typography sx={{ mb: 1, fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
              Output
            </Typography>
            {studio.dubbingResult ? (
              <Stack spacing={1.25}>
                <Stack direction="row" spacing={1}>
                  <Chip size="small" color="success" label={`${studio.dubbingResult.segment_count} segments`} />
                  <Chip size="small" variant="outlined" label={studio.dubbingResult.voice} />
                  {studio.dubbingResult.speakers.map((speaker) => (
                    <Chip key={speaker} size="small" variant="outlined" label={speaker} />
                  ))}
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`${studio.dubbingResult.source_language || "auto"} -> ${studio.dubbingResult.target_language}`}
                  />
                </Stack>
                <TextField label="Dubbed audio" value={studio.dubbingResult.dubbed_audio_path} InputProps={{ readOnly: true }} />
                <TextField label="Dubbed video" value={studio.dubbingResult.dubbed_video_path || ""} InputProps={{ readOnly: true }} />
                <TextField label="SRT subtitles" value={studio.dubbingResult.srt_path} InputProps={{ readOnly: true }} />
                <TextField label="VTT subtitles" value={studio.dubbingResult.vtt_path} InputProps={{ readOnly: true }} />
              </Stack>
            ) : (
              <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                Dubbed WAV, subtitles, and video path will appear here after processing.
              </Typography>
            )}
          </Paper>
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
