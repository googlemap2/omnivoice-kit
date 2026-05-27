import SaveAltIcon from "@mui/icons-material/SaveAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import { Box, Button, Chip, Paper, Stack, TextField, Typography } from "@mui/material";
import { WorkspaceShell } from "../../components/layout/WorkspaceShell";
import { SelectField } from "../../components/ui/SelectField";
import type { AppSettings, Meta, ModelStatus } from "../../types/api";

type SettingsPanelProps = {
  settings: AppSettings | null;
  setSettings: (settings: AppSettings) => void;
  statuses: ModelStatus[];
  meta: Meta;
  onSave: () => void;
};

export function SettingsPanel(props: SettingsPanelProps) {
  if (!props.settings) {
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
        <Button startIcon={<SaveAltIcon />} variant="contained" onClick={props.onSave}>
          Save
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <SelectField
            label="Default model"
            value={props.settings.default_model}
            onChange={(value) => props.setSettings({ ...props.settings!, default_model: value })}
            options={props.meta.omnivoice_models}
          />
          <SelectField
            label="Default device"
            value={props.settings.default_device || ""}
            onChange={(value) => props.setSettings({ ...props.settings!, default_device: value || null })}
            options={props.meta.devices.map((id) => ({ id, label: id || "auto" }))}
          />
          <SelectField
            label="Default effect"
            value={props.settings.default_effect_preset}
            onChange={(value) =>
              props.setSettings({
                ...props.settings!,
                default_effect_preset: value as AppSettings["default_effect_preset"],
              })
            }
            options={props.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <TextField
            label="Output directory"
            value={props.settings.output_dir}
            onChange={(event) => props.setSettings({ ...props.settings!, output_dir: event.target.value })}
          />
        </Stack>
        <Stack spacing={1}>
          {props.statuses.map((status) => (
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
