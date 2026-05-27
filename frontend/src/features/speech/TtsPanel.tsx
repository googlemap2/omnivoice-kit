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
import { WorkspaceShell } from "../../components/layout/WorkspaceShell";
import { SelectField } from "../../components/ui/SelectField";
import { SliderField } from "../../components/ui/SliderField";
import { type Meta, type Voice } from "../../types/api";
import type { GenerationMode } from "../../types/studio";
import { downloadBlob } from "../../lib/api";

type TtsPanelProps = {
  mode: GenerationMode;
  setMode: (mode: GenerationMode) => void;
  voices: Voice[];
  meta: Meta;
  selectedVoice: string;
  setSelectedVoice: (voice: string) => void;
  speechText: string;
  setSpeechText: (text: string) => void;
  language: string;
  setLanguage: (language: string) => void;
  effectPreset: "raw" | "normalize" | "broadcast";
  setEffectPreset: (preset: "raw" | "normalize" | "broadcast") => void;
  instructs: string[];
  setInstructs: (items: string[]) => void;
  numStep: number;
  setNumStep: (value: number) => void;
  guidanceScale: number;
  setGuidanceScale: (value: number) => void;
  speed: number;
  setSpeed: (value: number) => void;
  duration: string;
  setDuration: (value: string) => void;
  denoise: boolean;
  setDenoise: (value: boolean) => void;
  preprocessPrompt: boolean;
  setPreprocessPrompt: (value: boolean) => void;
  postprocessOutput: boolean;
  setPostprocessOutput: (value: boolean) => void;
  refText: string;
  setRefText: (value: string) => void;
  refAudio: File | null;
  setRefAudio: (file: File | null) => void;
  onGenerate: () => void;
  audioUrl: string | null;
  lastAudio: Blob | null;
};

export function TtsPanel(props: TtsPanelProps) {
  return (
    <WorkspaceShell
      icon={<MicIcon />}
      title="Speech Studio"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={props.onGenerate}>
          Generate
        </Button>
      }
    >
      <Tabs value={props.mode} onChange={(_, value) => props.setMode(value)}>
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
            value={props.speechText}
            onChange={(event) => props.setSpeechText(event.target.value)}
          />
          {props.mode === "clone" && (
            <Stack spacing={1.5}>
              <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
                {props.refAudio ? props.refAudio.name : "Choose reference audio"}
                <input
                  hidden
                  type="file"
                  accept="audio/*,video/*"
                  onChange={(event) => props.setRefAudio(event.target.files?.[0] || null)}
                />
              </Button>
              <TextField
                label="Reference transcript"
                value={props.refText}
                onChange={(event) => props.setRefText(event.target.value)}
              />
            </Stack>
          )}
          {props.audioUrl && (
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <audio controls src={props.audioUrl} style={{ width: "100%" }} />
                <Tooltip title="Download WAV">
                  <span>
                    <IconButton
                      disabled={!props.lastAudio}
                      onClick={() => props.lastAudio && downloadBlob(props.lastAudio, "speech.wav")}
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
          {props.mode === "speaker" && (
            <FormControl size="small">
              <InputLabel>Voice</InputLabel>
              <Select
                label="Voice"
                value={props.selectedVoice}
                onChange={(event) => props.setSelectedVoice(event.target.value)}
              >
                {props.voices.map((voice) => (
                  <MenuItem key={voice.id} value={voice.id}>
                    {voice.name || voice.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <SelectField label="Language" value={props.language} onChange={props.setLanguage} options={props.meta.languages} />
          <SelectField
            label="Effect"
            value={props.effectPreset}
            onChange={(value) => props.setEffectPreset(value as "raw" | "normalize" | "broadcast")}
            options={props.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <FormControl size="small">
            <InputLabel>Instruct items</InputLabel>
            <Select
              multiple
              label="Instruct items"
              value={props.instructs}
              onChange={(event) => props.setInstructs(event.target.value as string[])}
            >
              {props.meta.instructs.map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <SliderField label="Steps" value={props.numStep} min={4} max={64} step={1} onChange={props.setNumStep} />
          <SliderField
            label="Guidance"
            value={props.guidanceScale}
            min={0.5}
            max={5}
            step={0.1}
            onChange={props.setGuidanceScale}
          />
          <SliderField label="Speed" value={props.speed} min={0.5} max={2} step={0.05} onChange={props.setSpeed} />
          <TextField
            label="Duration seconds"
            type="number"
            value={props.duration}
            onChange={(event) => props.setDuration(event.target.value)}
          />
          <FormControlLabel
            control={<Switch checked={props.denoise} onChange={(event) => props.setDenoise(event.target.checked)} />}
            label="Denoise"
          />
          {props.mode !== "design" && (
            <FormControlLabel
              control={
                <Switch
                  checked={props.preprocessPrompt}
                  onChange={(event) => props.setPreprocessPrompt(event.target.checked)}
                />
              }
              label="Preprocess prompt"
            />
          )}
          <FormControlLabel
            control={
              <Switch
                checked={props.postprocessOutput}
                onChange={(event) => props.setPostprocessOutput(event.target.checked)}
              />
            }
            label="Postprocess output"
          />
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
