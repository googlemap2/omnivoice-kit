"use client";

import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import SaveAltIcon from "@mui/icons-material/SaveAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Box,
  Button,
  Chip,
  FormControlLabel,
  Paper,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { useStudio } from "../../../components/studio/StudioContext";
import { SelectField } from "../../../components/ui/SelectField";
import type { AppSettings } from "../../../types/api";

type SettingsTab =
  | "tts"
  | "modelProviders"
  | "translation"
  | "diagnostics"
  | "models";

export default function SettingsPage() {
  const studio = useStudio();
  const [tab, setTab] = useState<SettingsTab>("tts");

  function handleTabChange(value: SettingsTab) {
    setTab(value);
    if (value === "diagnostics" && !studio.diagnostics) {
      void studio.refreshDiagnostics();
    }
  }

  if (!studio.settings) {
    return (
      <WorkspaceShell icon={<SettingsIcon />} title="Settings">
        <Typography>Loading settings...</Typography>
      </WorkspaceShell>
    );
  }

  function updateProviderConfig(
    provider: string,
    field: string,
    value: string | boolean,
  ) {
    if (!studio.settings) return;
    const current = studio.settings.translation_provider_config || {};
    const providerConfig = current[provider];
    const nextProviderConfig =
      providerConfig &&
      typeof providerConfig === "object" &&
      !Array.isArray(providerConfig)
        ? { ...providerConfig, [field]: value }
        : { [field]: value };
    studio.setSettings({
      ...studio.settings,
      translation_provider_config: {
        ...current,
        [provider]: nextProviderConfig,
      },
    });
  }

  function updateModelProviderConfig(
    provider: string,
    field: string,
    value: string | boolean,
  ) {
    if (!studio.settings) return;
    const current = studio.settings.model_provider_config || {};
    const providerConfig = current[provider];
    const nextProviderConfig =
      providerConfig &&
      typeof providerConfig === "object" &&
      !Array.isArray(providerConfig)
        ? { ...providerConfig, [field]: value }
        : { [field]: value };
    studio.setSettings({
      ...studio.settings,
      model_provider_config: {
        ...current,
        default_provider: "cloud",
        [provider]: nextProviderConfig,
      },
    });
  }

  function modelProviderValue(provider: string, field: string) {
    const providerConfig = studio.settings?.model_provider_config?.[provider];
    if (
      !providerConfig ||
      typeof providerConfig !== "object" ||
      Array.isArray(providerConfig)
    )
      return "";
    const value = (providerConfig as Record<string, unknown>)[field];
    return typeof value === "string" ? value : "";
  }

  function providerValue(provider: string, field: string) {
    const providerConfig =
      studio.settings?.translation_provider_config?.[provider];
    if (
      !providerConfig ||
      typeof providerConfig !== "object" ||
      Array.isArray(providerConfig)
    )
      return "";
    const value = (providerConfig as Record<string, unknown>)[field];
    return typeof value === "string" ? value : "";
  }

  function providerBool(provider: string, field: string) {
    const providerConfig =
      studio.settings?.translation_provider_config?.[provider];
    if (
      !providerConfig ||
      typeof providerConfig !== "object" ||
      Array.isArray(providerConfig)
    )
      return false;
    return Boolean((providerConfig as Record<string, unknown>)[field]);
  }

  return (
    <WorkspaceShell
      icon={<SettingsIcon />}
      title="Settings"
      action={
        <Button
          startIcon={<SaveAltIcon />}
          variant="contained"
          onClick={studio.saveSettings}>
          Save
        </Button>
      }>
      <Tabs
        value={tab}
        onChange={(_, value) => handleTabChange(value)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}>
        <Tab value="tts" label="TTS Config" />
        <Tab value="modelProviders" label="Model Providers" />
        <Tab value="translation" label="Translation Providers" />
        <Tab value="diagnostics" label="Diagnostics" />
        <Tab value="models" label="Models" />
      </Tabs>

      {tab === "tts" && (
        <Box sx={{ maxWidth: 520 }}>
          <Stack spacing={2}>
            <SelectField
              label="Default model TTS"
              value={studio.settings.default_model}
              onChange={(value) =>
                studio.setSettings({
                  ...studio.settings!,
                  default_model: value,
                })
              }
              options={studio.meta.omnivoice_models}
            />
            <SelectField
              label="Default device"
              value={studio.settings.default_device || ""}
              onChange={(value) =>
                studio.setSettings({
                  ...studio.settings!,
                  default_device: value || null,
                })
              }
              options={studio.meta.devices.map((id) => ({
                id,
                label: id || "auto",
              }))}
            />
            <SelectField
              label="Default effect"
              value={studio.settings.default_effect_preset}
              onChange={(value) =>
                studio.setSettings({
                  ...studio.settings!,
                  default_effect_preset:
                    value as AppSettings["default_effect_preset"],
                })
              }
              options={studio.meta.effect_presets.map((id) => ({
                id,
                label: id,
              }))}
            />
            <TextField
              label="Output directory"
              value={studio.settings.output_dir}
              onChange={(event) =>
                studio.setSettings({
                  ...studio.settings!,
                  output_dir: event.target.value,
                })
              }
            />
          </Stack>
        </Box>
      )}

      {tab === "modelProviders" && (
        <Box sx={{ maxWidth: 720 }}>
          <Stack spacing={2}>
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Typography
                sx={{
                  mb: 1,
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}>
                Runtime Note
              </Typography>
              <Typography sx={{ fontSize: 13, color: "text.secondary" }}>
                These settings are saved for an OpenAI-compatible model
                endpoint. Local generation still uses OmniVoice unless the
                calling flow is wired to this cloud provider.
              </Typography>
            </Paper>
            <ProviderConfig title="OpenAI-compatible Cloud" providerId="cloud">
              <TextField
                label="Provider name"
                value={modelProviderValue("cloud", "provider_name")}
                onChange={(event) =>
                  updateModelProviderConfig(
                    "cloud",
                    "provider_name",
                    event.target.value,
                  )
                }
                placeholder="Provider name (e.g. OpenAI, Azure, etc.)"
              />
              <TextField
                label="Base URL"
                value={modelProviderValue("cloud", "base_url")}
                onChange={(event) =>
                  updateModelProviderConfig(
                    "cloud",
                    "base_url",
                    event.target.value,
                  )
                }
                placeholder="Base URL (e.g. https://api.openai.com/v1)"
              />
              <TextField
                label="API key"
                type="password"
                value={modelProviderValue("cloud", "api_key")}
                onChange={(event) =>
                  updateModelProviderConfig(
                    "cloud",
                    "api_key",
                    event.target.value,
                  )
                }
              />
              <TextField
                label="Default speech model"
                value={modelProviderValue("cloud", "speech_model")}
                onChange={(event) =>
                  updateModelProviderConfig(
                    "cloud",
                    "speech_model",
                    event.target.value,
                  )
                }
                placeholder="tts-1"
              />
              <TextField
                label="Default transcription model"
                value={modelProviderValue("cloud", "transcription_model")}
                onChange={(event) =>
                  updateModelProviderConfig(
                    "cloud",
                    "transcription_model",
                    event.target.value,
                  )
                }
                placeholder="whisper-1"
              />
            </ProviderConfig>
          </Stack>
        </Box>
      )}

      {tab === "translation" && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              lg: "minmax(360px, 520px) minmax(360px, 1fr)",
            },
            gap: 2,
          }}>
          <Stack spacing={2}>
            <SelectField
              label="Default provider"
              value={studio.settings.default_translation_provider}
              onChange={(value) =>
                studio.setSettings({
                  ...studio.settings!,
                  default_translation_provider: value,
                })
              }
              options={studio.providers.map((provider) => ({
                id: provider.id,
                label: provider.name,
              }))}
            />

            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Typography
                sx={{
                  mb: 1,
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}>
                Provider Status
              </Typography>
              <Stack spacing={0.75}>
                {studio.providers.map((provider) => (
                  <Chip
                    key={provider.id}
                    size="small"
                    color={provider.available ? "success" : "default"}
                    variant="outlined"
                    label={`${provider.id}${provider.available ? "" : " unavailable"}`}
                  />
                ))}
              </Stack>
            </Paper>
          </Stack>

          <Stack spacing={2}>
            <ProviderConfig title="Google" providerId="google">
              <TextField
                label="Google API key"
                type="password"
                value={providerValue("google", "api_key")}
                onChange={(event) =>
                  updateProviderConfig("google", "api_key", event.target.value)
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={providerBool("google", "disabled")}
                    onChange={(event) =>
                      updateProviderConfig(
                        "google",
                        "disabled",
                        event.target.checked,
                      )
                    }
                  />
                }
                label="Disable Google provider"
              />
            </ProviderConfig>

            <ProviderConfig title="DeepL" providerId="deepl">
              <TextField
                label="DeepL API key"
                type="password"
                value={providerValue("deepl", "api_key")}
                onChange={(event) =>
                  updateProviderConfig("deepl", "api_key", event.target.value)
                }
              />
            </ProviderConfig>

            <ProviderConfig title="Microsoft" providerId="microsoft">
              <TextField
                label="Microsoft API key"
                type="password"
                value={providerValue("microsoft", "api_key")}
                onChange={(event) =>
                  updateProviderConfig(
                    "microsoft",
                    "api_key",
                    event.target.value,
                  )
                }
              />
              <TextField
                label="Microsoft region"
                value={providerValue("microsoft", "region")}
                onChange={(event) =>
                  updateProviderConfig(
                    "microsoft",
                    "region",
                    event.target.value,
                  )
                }
              />
            </ProviderConfig>

            <ProviderConfig title="MyMemory" providerId="mymemory">
              <TextField
                label="MyMemory API key"
                type="password"
                value={providerValue("mymemory", "api_key")}
                onChange={(event) =>
                  updateProviderConfig(
                    "mymemory",
                    "api_key",
                    event.target.value,
                  )
                }
              />
            </ProviderConfig>

            <ProviderConfig title="NLLB Local" providerId="nllb">
              <TextField
                label="NLLB model id"
                value={providerValue("nllb", "model_id")}
                onChange={(event) =>
                  updateProviderConfig("nllb", "model_id", event.target.value)
                }
              />
            </ProviderConfig>
          </Stack>
        </Box>
      )}

      {tab === "diagnostics" && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "minmax(320px, 420px) 1fr" },
            gap: 2,
          }}>
          <Stack spacing={2}>
            <Button
              startIcon={<RefreshIcon />}
              variant="contained"
              onClick={studio.refreshDiagnostics}>
              Refresh Diagnostics
            </Button>
            <Button
              startIcon={<DeleteIcon />}
              variant="outlined"
              color="error"
              onClick={studio.clearLogs}>
              Clear Logs
            </Button>
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Typography
                sx={{
                  mb: 1,
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}>
                Quick Status
              </Typography>
              <Stack spacing={0.75}>
                <Chip
                  size="small"
                  color={
                    studio.diagnostics?.ffmpeg?.available
                      ? "success"
                      : "warning"
                  }
                  label={`ffmpeg: ${studio.diagnostics?.ffmpeg?.available ? "available" : "missing"}`}
                />
                <Chip
                  size="small"
                  color={
                    studio.diagnostics?.device?.cuda_available
                      ? "success"
                      : "default"
                  }
                  label={`cuda: ${studio.diagnostics?.device?.cuda_available ? "available" : "not available"}`}
                />
                <Chip
                  size="small"
                  color={
                    studio.diagnostics?.device?.mps_available
                      ? "success"
                      : "default"
                  }
                  label={`mps: ${studio.diagnostics?.device?.mps_available ? "available" : "not available"}`}
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={`models installed: ${studio.diagnostics?.models?.installed_count ?? 0}`}
                />
              </Stack>
            </Paper>
          </Stack>

          <Stack spacing={2}>
            <TextField
              label="Diagnostics JSON"
              multiline
              minRows={12}
              value={
                studio.diagnostics
                  ? JSON.stringify(studio.diagnostics, null, 2)
                  : ""
              }
              InputProps={{ readOnly: true }}
            />
            <TextField
              label="Logs"
              multiline
              minRows={12}
              value={studio.logs.join("\n")}
              InputProps={{ readOnly: true }}
            />
          </Stack>
        </Box>
      )}

      {tab === "models" && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "minmax(320px, 420px) 1fr" },
            gap: 2,
          }}>
          <Paper
            variant="outlined"
            sx={{ p: 1.5, bgcolor: "#252526", alignSelf: "start" }}>
            <Typography
              sx={{
                mb: 1,
                fontSize: 12,
                fontWeight: 700,
                textTransform: "uppercase",
              }}>
              Models
            </Typography>
            <Stack spacing={0.75}>
              <Chip
                size="small"
                label={`${studio.installedCount}/${studio.statuses.length || 0} installed`}
              />
              {studio.statuses.map((status) => (
                <Chip
                  key={status.repo_id}
                  size="small"
                  color={status.installed ? "success" : "warning"}
                  variant="outlined"
                  label={status.repo_id}
                />
              ))}
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
            <Typography
              sx={{
                mb: 1,
                fontSize: 12,
                fontWeight: 700,
                textTransform: "uppercase",
              }}>
              Model Details
            </Typography>
            <Stack spacing={1.5}>
              {studio.statuses.map((status) => (
                <Box key={status.repo_id}>
                  <Typography sx={{ fontWeight: 600 }}>
                    {status.repo_id}
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: 12,
                      color: "text.secondary",
                      overflowWrap: "anywhere",
                    }}>
                    {status.local_path}
                  </Typography>
                  <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    flexWrap="wrap"
                    sx={{ mt: 1 }}>
                    <Chip
                      size="small"
                      color={status.installed ? "success" : "warning"}
                      label={status.installed ? "installed" : "missing"}
                    />
                    <Chip
                      size="small"
                      variant="outlined"
                      label={status.has_config ? "config" : "no config"}
                    />
                    <Chip
                      size="small"
                      variant="outlined"
                      label={status.has_weights ? "weights" : "no weights"}
                    />
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Paper>
        </Box>
      )}
    </WorkspaceShell>
  );
}

function ProviderConfig({
  title,
  providerId,
  children,
}: {
  title: string;
  providerId: string;
  children: React.ReactNode;
}) {
  return (
    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
      <Typography
        sx={{
          mb: 1.5,
          fontSize: 12,
          fontWeight: 700,
          textTransform: "uppercase",
        }}>
        {title}{" "}
        <Typography
          component="span"
          sx={{ color: "text.secondary", fontSize: 12 }}>
          ({providerId})
        </Typography>
      </Typography>
      <Stack spacing={1.5}>{children}</Stack>
    </Paper>
  );
}
