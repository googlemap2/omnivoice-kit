import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SubtitlesIcon from "@mui/icons-material/Subtitles";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Stack, TextField } from "@mui/material";
import { WorkspaceShell } from "../../components/layout/WorkspaceShell";
import { SelectField } from "../../components/ui/SelectField";
import type { Meta } from "../../types/api";

type TranscribePanelProps = {
  meta: Meta;
  language: string;
  setLanguage: (language: string) => void;
  transcribeFile: File | null;
  setTranscribeFile: (file: File | null) => void;
  transcribeFormat: string;
  setTranscribeFormat: (format: string) => void;
  transcription: string;
  onTranscribe: () => void;
};

export function TranscribePanel(props: TranscribePanelProps) {
  return (
    <WorkspaceShell
      icon={<SubtitlesIcon />}
      title="Transcription"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={props.onTranscribe}>
          Run ASR
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {props.transcribeFile ? props.transcribeFile.name : "Choose media file"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => props.setTranscribeFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField label="Language" value={props.language} onChange={props.setLanguage} options={props.meta.languages} />
          <SelectField
            label="Output"
            value={props.transcribeFormat}
            onChange={props.setTranscribeFormat}
            options={props.meta.transcription_formats.map((id) => ({ id, label: id }))}
          />
        </Stack>
        <TextField
          label="Transcript output"
          multiline
          minRows={18}
          value={props.transcription}
          InputProps={{ readOnly: true }}
        />
      </Box>
    </WorkspaceShell>
  );
}
