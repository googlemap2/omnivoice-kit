"use client";

import CancelIcon from "@mui/icons-material/Cancel";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import QueueIcon from "@mui/icons-material/Queue";
import RefreshIcon from "@mui/icons-material/Refresh";
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
  Tooltip,
  Typography,
} from "@mui/material";
import type { ChipProps } from "@mui/material";
import { useEffect, useRef } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { useStudio } from "../../../components/studio/StudioContext";

export default function JobsPage() {
  const studio = useStudio();
  const refreshJobsRef = useRef(studio.refreshJobs);

  useEffect(() => {
    refreshJobsRef.current = studio.refreshJobs;
  }, [studio.refreshJobs]);

  useEffect(() => {
    void refreshJobsRef.current();
    const intervalId = window.setInterval(() => {
      void refreshJobsRef.current();
    }, 3000);
    return () => window.clearInterval(intervalId);
  }, []);

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
      <Box sx={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 2 }}>
        <Paper variant="outlined" sx={{ bgcolor: "#252526", overflow: "hidden", minWidth: 0 }}>
          <TableContainer sx={{ maxHeight: 620, overflowX: "auto" }}>
            <Table stickyHeader size="small" sx={{ minWidth: 720 }}>
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
                        {downloadArtifacts(job).map((artifact) => (
                          <Tooltip key={artifact.id} title={artifact.label}>
                            <IconButton size="small" onClick={() => studio.downloadJobOutput(job, artifact.id)}>
                              <DownloadIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ))}
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

function downloadArtifacts(job: {
  type: string;
  status: string;
  result: Record<string, unknown> | null;
}) {
  if (job.status !== "completed" || !job.result) return [];
  if (job.type === "speech" && typeof job.result.output_path === "string") {
    return [{ id: "primary", label: "Download speech WAV" }];
  }
  if (job.type === "dubbing") {
    const items = [];
    if (typeof job.result.dubbed_video_path === "string") items.push({ id: "video", label: "Download dubbed video" });
    if (typeof job.result.dubbed_audio_path === "string") items.push({ id: "audio", label: "Download dubbed audio" });
    if (typeof job.result.srt_path === "string") items.push({ id: "srt", label: "Download SRT" });
    if (typeof job.result.vtt_path === "string") items.push({ id: "vtt", label: "Download VTT" });
    if (typeof job.result.voice_manifest_path === "string") items.push({ id: "voices", label: "Download voice manifest" });
    return items;
  }
  if (job.type === "translation") {
    return [
      { id: "text", label: "Download text" },
      { id: "json", label: "Download JSON" },
    ];
  }
  if (job.type === "transcription") {
    const items = [];
    const format = typeof job.result.response_format === "string" ? job.result.response_format : "";
    if ((!format || format === "srt") && typeof job.result.raw_srt === "string") {
      items.push({ id: "raw_srt", label: "Download raw SRT" });
    }
    if ((!format || format === "srt") && typeof job.result.translated_srt === "string") {
      items.push({ id: "translated_srt", label: "Download translated SRT" });
    }
    if ((!format || format === "vtt") && typeof job.result.raw_vtt === "string") {
      items.push({ id: "raw_vtt", label: "Download raw VTT" });
    }
    if ((!format || format === "vtt") && typeof job.result.translated_vtt === "string") {
      items.push({ id: "translated_vtt", label: "Download translated VTT" });
    }
    items.push({ id: "json", label: "Download transcript JSON" });
    return items;
  }
  return [{ id: "json", label: "Download JSON" }];
}
