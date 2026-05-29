"use client";

import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import MicIcon from "@mui/icons-material/Mic";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SaveAltIcon from "@mui/icons-material/SaveAlt";
import StopIcon from "@mui/icons-material/Stop";
import SubtitlesIcon from "@mui/icons-material/Subtitles";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Box,
  Button,
  FormControlLabel,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  Switch,
} from "@mui/material";
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
      <Box sx={{ display: "grid", gridTemplateColumns: "320px minmax(0, 1fr)", gap: 2 }}>
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
          {/* <FormControlLabel
            control={
              <Switch
                checked={studio.transcribeQueued}
                onChange={(event) => studio.setTranscribeQueued(event.target.checked)}
              />
            }
            label="Send to queue"
          /> */}
          <Button
            startIcon={studio.dictationActive ? <StopIcon /> : <MicIcon />}
            variant={studio.dictationActive ? "contained" : "outlined"}
            color={studio.dictationActive ? "error" : "primary"}
            onClick={studio.dictationActive ? studio.stopDictation : studio.startDictation}
          >
            {studio.dictationActive ? "Stop dictation" : "Start dictation"}
          </Button>
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {studio.subtitleFile ? studio.subtitleFile.name : "Import subtitle"}
            <input
              hidden
              type="file"
              accept=".srt,.vtt,text/vtt,application/x-subrip"
              onChange={(event) => studio.setSubtitleFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField
            label="Subtitle format"
            value={studio.subtitleFormat}
            onChange={studio.setSubtitleFormat}
            options={studio.meta.subtitle_formats.map((id) => ({ id, label: id }))}
          />
          <Button startIcon={<SubtitlesIcon />} variant="outlined" onClick={studio.importSubtitles}>
            Import
          </Button>
          <Button startIcon={<SaveAltIcon />} variant="outlined" onClick={studio.exportSubtitles}>
            Export
          </Button>
        </Stack>
        <Stack spacing={2} sx={{ minWidth: 0 }}>
          <Paper variant="outlined" sx={{ bgcolor: "#252526", overflow: "hidden" }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ px: 1.5, py: 1 }}>
              <Typography sx={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                Subtitle Segments
              </Typography>
              <Button size="small" startIcon={<AddIcon />} onClick={studio.addSubtitleSegment}>
                Add
              </Button>
            </Stack>
            <TableContainer sx={{ maxHeight: 420 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ width: 88 }}>Start</TableCell>
                    <TableCell sx={{ width: 88 }}>End</TableCell>
                    <TableCell sx={{ width: 120 }}>Speaker</TableCell>
                    <TableCell>Text</TableCell>
                    <TableCell sx={{ width: 48 }} />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {studio.subtitleSegments.map((segment, index) => (
                    <TableRow key={`${segment.id}-${index}`}>
                      <TableCell>
                        <TextField
                          size="small"
                          type="number"
                          value={segment.start}
                          onChange={(event) =>
                            studio.updateSubtitleSegment(index, { start: Number(event.target.value) })
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          size="small"
                          type="number"
                          value={segment.end}
                          onChange={(event) =>
                            studio.updateSubtitleSegment(index, { end: Number(event.target.value) })
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          size="small"
                          value={segment.speaker || ""}
                          onChange={(event) =>
                            studio.updateSubtitleSegment(index, { speaker: event.target.value || null })
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          size="small"
                          fullWidth
                          multiline
                          minRows={1}
                          value={segment.text}
                          onChange={(event) => studio.updateSubtitleSegment(index, { text: event.target.value })}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Delete segment">
                          <IconButton size="small" onClick={() => studio.deleteSubtitleSegment(index)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {studio.subtitleSegments.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5}>
                        <Typography sx={{ py: 2, color: "text.secondary", fontSize: 13 }}>
                          Import subtitles or run ASR with verbose JSON to populate editable segments.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
          <TextField
            label="Raw transcript JSON"
            multiline
            minRows={8}
            value={studio.transcription}
            onChange={(event) => studio.setTranscription(event.target.value)}
          />
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
