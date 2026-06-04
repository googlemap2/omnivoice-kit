"use client";

import SendIcon from "@mui/icons-material/Send";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { apiJson } from "../../../lib/api";
import type { ProviderModel } from "../../../types/api";

export default function ProviderChatPage() {
  const [providers, setProviders] = useState<ProviderModel[]>([]);
  const [providerId, setProviderId] = useState("");
  const [model, setModel] = useState("");
  const [system, setSystem] = useState("You are a concise helpful assistant.");
  const [message, setMessage] = useState("Xin chào, hãy trả lời ngắn gọn bằng tiếng Việt.");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeProvider = providers.find((provider) => provider.id === providerId) || providers[0] || null;
  const modelOptions = useMemo(() => providerModelOptions(activeProvider), [activeProvider]);

  const refreshProviders = useCallback(async () => {
    setError(null);
    try {
      const result = await apiJson<{ data: ProviderModel[] }>("/v1/provider-models");
      setProviders(result.data);
      if (!providerId && result.data[0]?.id) {
        setProviderId(result.data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setProviders([]);
    }
  }, [providerId]);

  useEffect(() => {
    void refreshProviders();
  }, [refreshProviders]);

  useEffect(() => {
    if (model && modelOptions.some((option) => option.id === model)) return;
    setModel(modelOptions[0]?.id || "");
  }, [model, modelOptions]);

  async function sendMessage() {
    if (!activeProvider) {
      setError("Chưa có Model Provider. Hãy thêm provider trong Settings trước.");
      return;
    }
    if (!message.trim()) {
      setError("Message không được để trống.");
      return;
    }
    setLoading(true);
    setError(null);
    setAnswer("");
    try {
      const result = await apiJson<{ data: { content: string } }>("/v1/provider-models/chat", {
        method: "POST",
        body: JSON.stringify({
          provider_model_id: activeProvider.id,
          model: model || null,
          system: system || null,
          message,
          temperature: 0.2,
        }),
      });
      setAnswer(result.data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <WorkspaceShell icon={<SmartToyIcon />} title="Provider Chat">
      <Stack spacing={2} sx={{ maxWidth: 980 }}>
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6">Test Model Provider</Typography>
                <Typography variant="body2" color="text.secondary">
                  Gửi chat completion trực tiếp tới provider OpenAI-compatible đã cấu hình trong Settings.
                </Typography>
              </Box>

              {error && <Alert severity="error">{error}</Alert>}
              {!error && providers.length === 0 && (
                <Alert severity="info">Chưa có Model Provider. Vào Settings → Model Providers để thêm base URL và API key.</Alert>
              )}

              <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <TextField
                  select
                  label="Provider"
                  value={activeProvider?.id || ""}
                  onChange={(event) => setProviderId(event.target.value)}
                  fullWidth
                >
                  {providers.map((provider) => (
                    <MenuItem key={provider.id} value={provider.id}>
                      {provider.provider_name} — {provider.base_url}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  select
                  label="Model"
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                  fullWidth
                >
                  <MenuItem value="">Auto</MenuItem>
                  {modelOptions.map((option) => (
                    <MenuItem key={option.id} value={option.id}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Stack>

              <TextField
                label="System prompt"
                value={system}
                onChange={(event) => setSystem(event.target.value)}
                multiline
                minRows={2}
                fullWidth
              />
              <TextField
                label="Message"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                multiline
                minRows={4}
                fullWidth
              />

              <Stack direction="row" spacing={1}>
                <Button variant="contained" startIcon={loading ? <CircularProgress size={16} /> : <SendIcon />} onClick={sendMessage} disabled={loading || !activeProvider}>
                  Send
                </Button>
                <Button variant="outlined" onClick={refreshProviders} disabled={loading}>
                  Refresh Providers
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Response
            </Typography>
            <Box
              component="pre"
              sx={{
                m: 0,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "monospace",
                minHeight: 160,
              }}
            >
              {answer || "No response yet."}
            </Box>
          </CardContent>
        </Card>
      </Stack>
    </WorkspaceShell>
  );
}

function providerModelOptions(provider: ProviderModel | null) {
  const config = provider?.config || {};
  const availableModels = config.available_models;
  if (Array.isArray(availableModels)) {
    return availableModels
      .filter((item): item is string => typeof item === "string" && item.trim().length > 0)
      .map((id) => ({ id, label: id }));
  }
  return [];
}
