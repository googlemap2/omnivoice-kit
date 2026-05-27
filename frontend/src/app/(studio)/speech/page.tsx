"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import MicIcon from "@mui/icons-material/Mic";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SaveAltIcon from "@mui/icons-material/SaveAlt";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Box,
  Button,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Tooltip,
} from "@mui/material";
import type { WheelEvent } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { SliderField } from "../../../components/ui/SliderField";
import { useStudio } from "../../../components/studio/StudioContext";
import { downloadBlob } from "../../../lib/api";

export default function SpeechPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<MicIcon />}
      title="Speech Studio"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={studio.generateSpeech}>
          Generate
        </Button>
      }
    >
      <Tabs value={studio.mode} onChange={(_, value) => studio.setMode(value)}>
        <Tab value="speaker" label="Speaker ID" />
        <Tab value="clone" label="Reference Clone" />
        <Tab value="design" icon={<AutoAwesomeIcon fontSize="small" />} iconPosition="start" label="Voice Design" />
      </Tabs>
      <Box sx={{ display: "grid", gridTemplateColumns: "minmax(360px, 1fr) 320px", gap: 2, mt: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Input text"
            multiline
            minRows={8}
            value={studio.speechText}
            onChange={(event) => studio.setSpeechText(event.target.value)}
          />
          {studio.mode === "clone" && (
            <Stack spacing={1.5}>
              <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
                {studio.refAudio ? studio.refAudio.name : "Choose reference audio"}
                <input
                  hidden
                  type="file"
                  accept="audio/*,video/*"
                  onChange={(event) => studio.setRefAudio(event.target.files?.[0] || null)}
                />
              </Button>
              <TextField
                label="Reference transcript"
                value={studio.refText}
                onChange={(event) => studio.setRefText(event.target.value)}
              />
            </Stack>
          )}
          {studio.audioUrl && (
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <audio controls src={studio.audioUrl} style={{ width: "100%" }} />
                <Tooltip title="Download WAV">
                  <span>
                    <IconButton
                      disabled={!studio.lastAudio}
                      onClick={() => studio.lastAudio && downloadBlob(studio.lastAudio, "speech.wav")}
                    >
                      <SaveAltIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>
            </Paper>
          )}
        </Stack>
        <Stack spacing={2}>
          {studio.mode === "speaker" && (
            <FormControl size="small">
              <InputLabel>Voice</InputLabel>
              <Select
                label="Voice"
                value={studio.selectedVoice}
                onChange={(event) => studio.setSelectedVoice(event.target.value)}
              >
                {studio.voices.map((voice) => (
                  <MenuItem key={voice.id} value={voice.id}>
                    {voice.name || voice.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <SelectField label="Language" value={studio.language} onChange={studio.setLanguage} options={studio.meta.languages} />
          <SelectField
            label="Effect"
            value={studio.effectPreset}
            onChange={(value) => studio.setEffectPreset(value as "raw" | "normalize" | "broadcast")}
            options={studio.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <FormControl size="small">
            <InputLabel>Instruct items</InputLabel>
            <Select
              multiple
              label="Instruct items"
              value={studio.instructs}
              onChange={(event) => studio.setInstructs(event.target.value as string[])}
            >
              {studio.meta.instructs.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <SliderField label="Steps" value={studio.numStep} min={4} max={64} step={1} onChange={studio.setNumStep} />
          <SliderField
            label="Guidance"
            value={studio.guidanceScale}
            min={0.5}
            max={5}
            step={0.1}
            onChange={studio.setGuidanceScale}
          />
          <SliderField label="Speed" value={studio.speed} min={0.5} max={2} step={0.05} onChange={studio.setSpeed} />
          <TextField
            label="Duration seconds"
            type="number"
            value={studio.duration}
            onChange={(event) => studio.setDuration(event.target.value)}
            slotProps={{
              htmlInput: {
                onWheel: (event: WheelEvent<HTMLInputElement>) => event.currentTarget.blur(),
              },
            }}
          />
          <FormControlLabel
            control={<Switch checked={studio.denoise} onChange={(event) => studio.setDenoise(event.target.checked)} />}
            label="Denoise"
          />
          {studio.mode !== "design" && (
            <FormControlLabel
              control={
                <Switch
                  checked={studio.preprocessPrompt}
                  onChange={(event) => studio.setPreprocessPrompt(event.target.checked)}
                />
              }
              label="Preprocess prompt"
            />
          )}
          <FormControlLabel
            control={
              <Switch
                checked={studio.postprocessOutput}
                onChange={(event) => studio.setPostprocessOutput(event.target.checked)}
              />
            }
            label="Postprocess output"
          />
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
