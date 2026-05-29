"use client";

import CancelIcon from "@mui/icons-material/Cancel";
import DeleteIcon from "@mui/icons-material/Delete";
import QueueIcon from "@mui/icons-material/Queue";
import RefreshIcon from "@mui/icons-material/Refresh";
import SendIcon from "@mui/icons-material/Send";
import {
  Box,
  Button,
  Chip,
  IconButton,
  LinearProgress,
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
} from "@mui/material";
import type { ChipProps } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";

export default function JobsPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<QueueIcon />}
      title="Jobs"
      action={
        <Button startIcon={<RefreshIcon />} variant="outlined" onClick={studio.refreshJobs}>
          Refresh
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "320px minmax(0, 1fr)", gap: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Translation text"
            multiline
            minRows={5}
            value={studio.translateText}
            onChange={(event) => studio.setTranslateText(event.target.value)}
          />
          <SelectField
            label="Source language"
            value={studio.sourceLanguage}
            onChange={studio.setSourceLanguage}
            options={studio.meta.translation_languages}
          />
          <SelectField
            label="Target language"
            value={studio.targetLanguage}
            onChange={studio.setTargetLanguage}
            options={studio.meta.translation_languages}
          />
          <SelectField
            label="Provider"
            value={studio.provider}
            onChange={studio.setProvider}
            options={studio.providers.map((item) => ({ id: item.id, label: item.name }))}
          />
          <Button startIcon={<SendIcon />} variant="contained" onClick={studio.createTranslationJob}>
            Queue translation
          </Button>
        </Stack>
        <Paper variant="outlined" sx={{ bgcolor: "#252526", overflow: "hidden", minWidth: 0 }}>
          <TableContainer sx={{ maxHeight: 620 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: 150 }}>Job</TableCell>
                  <TableCell sx={{ width: 110 }}>Type</TableCell>
                  <TableCell sx={{ width: 130 }}>Status</TableCell>
                  <TableCell>Result / Error</TableCell>
                  <TableCell sx={{ width: 96 }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {studio.jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Typography sx={{ fontSize: 12, fontFamily: "monospace" }}>{job.id.slice(0, 8)}</Typography>
                      <Typography sx={{ fontSize: 11, color: "text.secondary" }}>{new Date(job.created_at).toLocaleString()}</Typography>
                    </TableCell>
                    <TableCell>{job.type}</TableCell>
                    <TableCell>
                      <Stack spacing={0.75}>
                        <Chip size="small" color={statusColor(job.status)} label={job.status} />
                        {(job.status === "pending" || job.status === "running") && (
                          <LinearProgress variant="determinate" value={Math.round((job.progress || 0) * 100)} />
                        )}
                      </Stack>
                    </TableCell>
                    <TableCell sx={{ minWidth: 0 }}>
                      <Typography
                        sx={{
                          fontSize: 12,
                          color: job.error ? "error.main" : "text.secondary",
                          maxWidth: 640,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {job.error || summarizeResult(job.result) || summarizeParams(job.params)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title="Cancel job">
                          <span>
                            <IconButton
                              size="small"
                              disabled={!["pending", "running"].includes(job.status)}
                              onClick={() => studio.cancelJob(job.id)}
                            >
                              <CancelIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Delete job">
                          <IconButton size="small" onClick={() => studio.deleteJob(job.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {studio.jobs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Typography sx={{ py: 2, color: "text.secondary", fontSize: 13 }}>
                        No queued jobs found.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>
    </WorkspaceShell>
  );
}

function statusColor(status: string): ChipProps["color"] {
  if (status === "completed") return "success";
  if (status === "failed") return "error";
  if (status === "running") return "primary";
  if (status === "canceled") return "default";
  return "warning";
}

function summarizeResult(result: Record<string, unknown> | null) {
  if (!result) return "";
  if (typeof result.text === "string") return result.text;
  if (typeof result.output_path === "string") return result.output_path;
  if (typeof result.dubbed_audio_path === "string") return result.dubbed_audio_path;
  return JSON.stringify(result);
}

function summarizeParams(params: Record<string, unknown>) {
  if (typeof params.text === "string") return params.text;
  if (typeof params.input_path === "string") return params.input_path;
  return JSON.stringify(params);
}
