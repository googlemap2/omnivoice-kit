"use client";

import MovieIcon from "@mui/icons-material/Movie";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Chip, FormControlLabel, IconButton, Paper, Stack, Switch, TextField, Typography } from "@mui/material";
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
          <TextField
            label="Output folder name"
            value={studio.dubbingFolderName}
            onChange={(event) => studio.setDubbingFolderName(event.target.value)}
          />
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
          {studio.dubbingDiarize && (
            <Paper variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                <Typography sx={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                  Speaker voices
                </Typography>
                <Button size="small" startIcon={<AddIcon />} onClick={studio.addDubbingSpeakerVoice}>
                  Add
                </Button>
              </Stack>
              <Stack spacing={1}>
                {Object.entries(studio.dubbingSpeakerVoiceMap).map(([speaker, mappedVoice]) => (
                  <Stack key={speaker} direction="row" spacing={1} alignItems="center">
                    <TextField
                      size="small"
                      label="Speaker"
                      value={speaker}
                      onChange={(event) => {
                        studio.deleteDubbingSpeakerVoice(speaker);
                        studio.setDubbingSpeakerVoice(event.target.value, mappedVoice);
                      }}
                      sx={{ width: 130 }}
                    />
                    <Box sx={{ flex: 1 }}>
                      <SelectField
                        label="Voice"
                        value={mappedVoice}
                        onChange={(voice) => studio.setDubbingSpeakerVoice(speaker, voice)}
                        options={studio.voices.map((voice) => ({ id: voice.id, label: voice.name || voice.id }))}
                      />
                    </Box>
                    <IconButton size="small" onClick={() => studio.deleteDubbingSpeakerVoice(speaker)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                ))}
                {Object.keys(studio.dubbingSpeakerVoiceMap).length === 0 && (
                  <Typography sx={{ color: "text.secondary", fontSize: 12 }}>
                    Add SPEAKER_00, SPEAKER_01 mappings to use different voice profiles.
                  </Typography>
                )}
              </Stack>
            </Paper>
          )}
          <FormControlLabel
            control={
              <Switch
                checked={studio.dubbingQueued}
                onChange={(event) => studio.setDubbingQueued(event.target.checked)}
              />
            }
            label="Send to queue"
          />
        </Stack>

        <Stack spacing={2}>
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
            <Typography sx={{ mb: 1, fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
              Output
            </Typography>
            {studio.dubbingResult ? (
              <Stack spacing={1.25}>
                {studio.dubbingVideoUrl && (
                  <Box
                    component="video"
                    src={studio.dubbingVideoUrl}
                    controls
                    sx={{
                      width: "100%",
                      maxHeight: 420,
                      bgcolor: "#111111",
                      border: "1px solid",
                      borderColor: "divider",
                    }}
                  />
                )}
                {studio.dubbingAudioUrl && !studio.dubbingVideoUrl && (
                  <Box
                    component="audio"
                    src={studio.dubbingAudioUrl}
                    controls
                    sx={{ width: "100%" }}
                  />
                )}
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ minWidth: 0 }}>
                  <Chip
                    size="small"
                    color="primary"
                    label={studio.dubbingResult.folder_name}
                    sx={{
                      maxWidth: 360,
                      "& .MuiChip-label": {
                        display: "block",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      },
                    }}
                  />
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
