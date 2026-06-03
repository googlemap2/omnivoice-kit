"use client";

import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import SaveAltIcon from "@mui/icons-material/SaveAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
import { apiJson } from "../../../lib/api";
import type { AppSettings } from "../../../types/api";

type SettingsTab =
  | "tts"
  | "modelProviders"
  | "translation"
  | "diagnostics"
  | "models";
type CloudProviderDraft = {
  provider_name: string;
  base_url: string;
  api_key: string;
};
type ProviderModelRecord = {
  id: string;
  provider_name: string;
  provider_type: string;
  base_url: string;
  api_key: string | null;
  config: Record<string, unknown> | null;
};

export default function SettingsPage() {
  const studio = useStudio();
  const [tab, setTab] = useState<SettingsTab>("tts");
  const [providerModels, setProviderModels] = useState<ProviderModelRecord[]>([]);
  const [providerModelsError, setProviderModelsError] = useState<string | null>(null);
  const [providerModelsLoading, setProviderModelsLoading] = useState(false);
  const [executingProviderId, setExecutingProviderId] = useState<string | null>(null);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [providerDialogMode, setProviderDialogMode] = useState<"add" | "edit">(
    "add",
  );
  const [editingProviderId, setEditingProviderId] = useState<string | null>(null);
  const [providerDraft, setProviderDraft] = useState<CloudProviderDraft>({
    provider_name: "",
    base_url: "",
    api_key: "",
  });
  const [providerSaveError, setProviderSaveError] = useState<string | null>(
    null,
  );
  const [providerSaving, setProviderSaving] = useState(false);

  function handleTabChange(value: SettingsTab) {
    setTab(value);
    if (value === "diagnostics" && !studio.diagnostics) {
      void studio.refreshDiagnostics();
    }
    if (value === "modelProviders") {
      void refreshProviderModels();
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

  async function refreshProviderModels() {
    setProviderModelsLoading(true);
    setProviderModelsError(null);
    try {
      const result = await apiJson<{ data: ProviderModelRecord[] }>("/v1/provider-models");
      setProviderModels(result.data);
    } catch (err) {
      setProviderModelsError(err instanceof Error ? err.message : String(err));
    } finally {
      setProviderModelsLoading(false);
    }
  }

  function openProviderDialog(mode: "add" | "edit", provider?: ProviderModelRecord) {
    setProviderDialogMode(mode);
    setEditingProviderId(mode === "edit" && provider ? provider.id : null);
    setProviderSaveError(null);
    setProviderDraft(
      mode === "edit" && provider
        ? {
            provider_name: provider.provider_name,
            base_url: provider.base_url,
            api_key: provider.api_key || "",
          }
        : {
            provider_name: "",
            base_url: "",
            api_key: "",
          },
    );
    setProviderDialogOpen(true);
  }

  async function saveProviderDraft() {
    setProviderSaving(true);
    setProviderSaveError(null);
    try {
      const path =
        providerDialogMode === "edit" && editingProviderId
          ? `/v1/provider-models/${encodeURIComponent(editingProviderId)}`
          : "/v1/provider-models";
      const method = providerDialogMode === "edit" ? "PATCH" : "POST";
      await apiJson<{ data: ProviderModelRecord }>(path, {
        method,
        body: JSON.stringify(providerDraft),
      });
      await refreshProviderModels();
      setProviderDialogOpen(false);
    } catch (err) {
      setProviderSaveError(err instanceof Error ? err.message : String(err));
    } finally {
      setProviderSaving(false);
    }
  }

  function providerModelStringArray(provider: ProviderModelRecord, field: string) {
    const value = provider.config?.[field];
    return Array.isArray(value)
      ? value.filter((item): item is string => typeof item === "string")
      : [];
  }

  async function loadCloudModels(provider: ProviderModelRecord) {
    setExecutingProviderId(provider.id);
    setProviderModelsError(null);
    try {
      await apiJson<{ data: Array<{ id?: string }> }>(`/v1/provider-models/${encodeURIComponent(provider.id)}/models`, {
        method: "POST",
      });
      await refreshProviderModels();
    } catch (err) {
      setProviderModelsError(err instanceof Error ? err.message : String(err));
    } finally {
      setExecutingProviderId(null);
    }
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
        tab === "modelProviders" ? undefined : (
        <Button
          startIcon={<SaveAltIcon />}
          variant="contained"
          onClick={studio.saveSettings}>
          Save
        </Button>
        )
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
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button variant="contained" onClick={() => openProviderDialog("add")}>
                Add Provider
              </Button>
              <Button variant="outlined" onClick={refreshProviderModels} disabled={providerModelsLoading}>
                {providerModelsLoading ? "Refreshing..." : "Refresh"}
              </Button>
            </Stack>

            {providerModelsError && (
              <Typography sx={{ color: "error.main", fontSize: 13 }}>
                {providerModelsError}
              </Typography>
            )}
            {providerModels.length === 0 ? (
              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
                <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                  No provider models found in database. Add a provider to continue.
                </Typography>
              </Paper>
            ) : (
              providerModels.map((provider) => {
                const availableModels = providerModelStringArray(provider, "available_models");
                const isExecuting = executingProviderId === provider.id;
                return (
                  <Paper key={provider.id} variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
                    <Stack spacing={1.25}>
                      <Typography
                        sx={{
                          fontSize: 12,
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}>
                        Provider
                      </Typography>
                      <Typography sx={{ fontWeight: 600 }}>{provider.provider_name}</Typography>
                      <Typography
                        sx={{
                          color: "text.secondary",
                          fontSize: 13,
                          overflowWrap: "anywhere",
                        }}>
                        {provider.base_url || "No base URL configured."}
                      </Typography>
                      <Typography
                        sx={{
                          color: "text.secondary",
                          fontSize: 11,
                          overflowWrap: "anywhere",
                        }}>
                        ID: {provider.id}
                      </Typography>
                      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                        <Chip
                          size="small"
                          color={provider.base_url ? "success" : "warning"}
                          label={provider.base_url ? "configured" : "missing base URL"}
                        />
                        <Chip
                          size="small"
                          variant="outlined"
                          label={provider.api_key ? "API key set" : "no API key"}
                        />
                      </Stack>
                      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => openProviderDialog("edit", provider)}>
                          Edit
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => loadCloudModels(provider)}
                          disabled={isExecuting}>
                          {isExecuting ? "Loading..." : "Execute"}
                        </Button>
                      </Stack>
                      <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#1e1e1e" }}>
                        <Typography
                          sx={{
                            mb: 1,
                            fontSize: 12,
                            fontWeight: 700,
                            textTransform: "uppercase",
                          }}>
                          Cloud Models
                        </Typography>
                        {availableModels.length > 0 ? (
                          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                            {availableModels.map((modelId) => (
                              <Chip
                                key={modelId}
                                size="small"
                                variant="outlined"
                                label={modelId}
                              />
                            ))}
                          </Stack>
                        ) : (
                          <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                            Execute the provider request to load cloud models.
                          </Typography>
                        )}
                      </Paper>
                    </Stack>
                  </Paper>
                );
              })
            )}

            <Dialog
              open={providerDialogOpen}
              onClose={() => setProviderDialogOpen(false)}
              fullWidth
              maxWidth="sm">
              <DialogTitle>
                {providerDialogMode === "add" ? "Add Provider" : "Edit Provider"}
              </DialogTitle>
              <DialogContent>
                <Stack spacing={2} sx={{ pt: 1 }}>
                  <TextField
                    label="Provider name"
                    value={providerDraft.provider_name}
                    onChange={(event) =>
                      setProviderDraft({
                        ...providerDraft,
                        provider_name: event.target.value,
                      })
                    }
                    placeholder="Provider name (e.g. OpenAI, Azure, etc.)"
                  />
                  <TextField
                    label="Base URL"
                    value={providerDraft.base_url}
                    onChange={(event) =>
                      setProviderDraft({
                        ...providerDraft,
                        base_url: event.target.value,
                      })
                    }
                    placeholder="Base URL (e.g. https://api.openai.com/v1)"
                  />
                  <TextField
                    label="API key"
                    type="password"
                    value={providerDraft.api_key}
                    onChange={(event) =>
                      setProviderDraft({
                        ...providerDraft,
                        api_key: event.target.value,
                      })
                    }
                  />
                  {providerSaveError && (
                    <Typography sx={{ color: "error.main", fontSize: 13 }}>
                      {providerSaveError}
                    </Typography>
                  )}
                </Stack>
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setProviderDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  onClick={saveProviderDraft}
                  disabled={providerSaving}>
                  {providerSaving ? "Saving..." : "Save"}
                </Button>
              </DialogActions>
            </Dialog>
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
