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
import { useCallback, useEffect, useMemo, useState } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";
import { apiJson } from "../../../lib/api";
import type { ProviderModel } from "../../../types/api";

export default function TranscriptionPage() {
  const studio = useStudio();
  const [providerModels, setProviderModels] = useState<ProviderModel[]>([]);
  const transcribeProviderModelId = studio.transcribeProviderModelId;
  const setTranscribeProviderModelId = studio.setTranscribeProviderModelId;
  const availableProviders = studio.providers.filter((provider) => provider.available);
  const activeProvider =
    availableProviders.find((provider) => provider.id === studio.provider)?.id ||
    availableProviders.find((provider) => provider.id !== "passthrough")?.id ||
    availableProviders[0]?.id ||
    studio.provider;
  const activeProviderModel =
    providerModels.find((provider) => provider.id === studio.transcribeProviderModelId) || providerModels[0] || null;
  const activeProviderModelOptions = useMemo(() => {
    const availableModels = activeProviderModel?.config?.available_models;
    return Array.isArray(availableModels)
      ? availableModels
          .filter((item): item is string => typeof item === "string" && item.trim().length > 0)
          .map((id) => ({ id, label: id }))
      : [];
  }, [activeProviderModel]);

  const refreshProviderModels = useCallback(async () => {
    try {
      const result = await apiJson<{ data: ProviderModel[] }>("/v1/provider-models");
      setProviderModels(result.data);
      if (!transcribeProviderModelId && result.data[0]?.id) {
        setTranscribeProviderModelId(result.data[0].id);
      }
    } catch {
      setProviderModels([]);
    }
  }, [setTranscribeProviderModelId, transcribeProviderModelId]);

  useEffect(() => {
    void refreshProviderModels();
  }, [refreshProviderModels]);

  function toggleTranslate() {
    const next = !studio.transcribeTranslate;
    if (next) {
      if (studio.transcribeTranslationMode === "provider" && activeProvider !== studio.provider) {
        studio.setProvider(activeProvider);
      }
      if (studio.transcribeTranslationMode === "model" && !studio.transcribeProviderModelId && providerModels[0]?.id) {
        studio.setTranscribeProviderModelId(providerModels[0].id);
      }
    }
    studio.setTranscribeTranslate(next);
  }

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
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "320px minmax(0, 1fr)" }, gap: 2 }}>
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
          <FormControlLabel
            control={
              <Switch
                checked={studio.transcribeQueued}
                onChange={(event) => studio.setTranscribeQueued(event.target.checked)}
              />
            }
            label="Send to queue"
          />
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
          <FormControlLabel
            control={<Switch checked={studio.transcribeTranslate} onChange={toggleTranslate} />}
            label="Translate"
          />
          {studio.transcribeTranslate && (
            <Paper variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
              <Stack spacing={1}>
                <SelectField
                  label="Engine"
                  value={studio.transcribeTranslationMode}
                  onChange={(value) => studio.setTranscribeTranslationMode(value as "provider" | "model")}
                  options={[
                    { id: "provider", label: "Translation provider" },
                    { id: "model", label: "Model provider" },
                  ]}
                />
                {studio.transcribeTranslationMode === "provider" ? (
                  <SelectField
                    label="Provider"
                    value={studio.provider}
                    onChange={studio.setProvider}
                    options={(availableProviders.length ? availableProviders : studio.providers).map((provider) => ({
                      id: provider.id,
                      label: provider.available ? provider.name : `${provider.name} (unavailable)`,
                    }))}
                  />
                ) : (
                  <>
                    <SelectField
                      label="Model provider"
                      value={studio.transcribeProviderModelId}
                      onChange={studio.setTranscribeProviderModelId}
                      options={
                        providerModels.length > 0
                          ? providerModels.map((provider) => ({
                              id: provider.id,
                              label: provider.provider_name || provider.base_url || provider.id,
                            }))
                          : [{ id: "", label: "No model providers" }]
                      }
                    />
                    {activeProviderModelOptions.length > 0 && (
                      <SelectField
                        label="Model"
                        value={studio.transcribeProviderModelName}
                        onChange={studio.setTranscribeProviderModelName}
                        options={[{ id: "", label: "Auto" }, ...activeProviderModelOptions]}
                      />
                    )}
                  </>
                )}
                <SelectField
                  label="Source"
                  value={studio.sourceLanguage}
                  onChange={studio.setSourceLanguage}
                  options={studio.meta.translation_languages}
                />
                <SelectField
                  label="Target"
                  value={studio.targetLanguage}
                  onChange={studio.setTargetLanguage}
                  options={studio.meta.translation_languages}
                />
              </Stack>
            </Paper>
          )}
        </Stack>
        <Stack spacing={2} sx={{ minWidth: 0 }}>
          <Paper variant="outlined" sx={{ bgcolor: "#252526", overflow: "hidden" }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "stretch", sm: "center" }}
              spacing={1}
              sx={{ px: 1.5, py: 1 }}
            >
              <Typography sx={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase" }}>
                Subtitle Segments
              </Typography>
              <Button size="small" startIcon={<AddIcon />} onClick={studio.addSubtitleSegment}>
                Add
              </Button>
            </Stack>
            <TableContainer sx={{ maxHeight: 420, overflowX: "auto" }}>
              <Table stickyHeader size="small" sx={{ minWidth: 620 }}>
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
