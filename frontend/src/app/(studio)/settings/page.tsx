"use client";

import SaveAltIcon from "@mui/icons-material/SaveAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";
import type { AppSettings } from "../../../types/api";

export default function SettingsPage() {
  const studio = useStudio();

  if (!studio.settings) {
    return (
      <WorkspaceShell icon={<SettingsIcon />} title="Settings">
        <Typography>Loading settings...</Typography>
      </WorkspaceShell>
    );
  }

  return (
    <WorkspaceShell
      icon={<SettingsIcon />}
      title="Settings"
      action={
        <Button startIcon={<SaveAltIcon />} variant="contained" onClick={studio.saveSettings}>
          Save
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <SelectField
            label="Default model TTS"
            value={studio.settings.default_model}
            onChange={(value) => studio.setSettings({ ...studio.settings!, default_model: value })}
            options={studio.meta.omnivoice_models}
          />
          <SelectField
            label="Default device"
            value={studio.settings.default_device || ""}
            onChange={(value) => studio.setSettings({ ...studio.settings!, default_device: value || null })}
            options={studio.meta.devices.map((id) => ({ id, label: id || "auto" }))}
          />
          <SelectField
            label="Default effect"
            value={studio.settings.default_effect_preset}
            onChange={(value) =>
              studio.setSettings({
                ...studio.settings!,
                default_effect_preset: value as AppSettings["default_effect_preset"],
              })
            }
            options={studio.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <TextField
            label="Output directory"
            value={studio.settings.output_dir}
            onChange={(event) => studio.setSettings({ ...studio.settings!, output_dir: event.target.value })}
          />
        </Stack>
        <Stack spacing={1}>
          {studio.statuses.map((status) => (
            <Paper key={status.repo_id} variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Typography sx={{ fontWeight: 600 }}>{status.repo_id}</Typography>
              <Typography sx={{ fontSize: 12, color: "text.secondary" }}>{status.local_path}</Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Chip
                  size="small"
                  color={status.installed ? "success" : "warning"}
                  label={status.installed ? "installed" : "missing"}
                />
                <Chip size="small" variant="outlined" label={status.has_config ? "config" : "no config"} />
                <Chip size="small" variant="outlined" label={status.has_weights ? "weights" : "no weights"} />
              </Stack>
            </Paper>
          ))}
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
