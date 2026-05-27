"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  API_BASE_URL,
  type AppSettings,
  type HistoryEntry,
  type Meta,
  type ModelStatus,
  type TranslationProvider,
  type Voice,
  apiAudio,
  apiForm,
  apiJson,
} from "../../lib/api";
import { emptyMeta } from "../../types/api";
import type { GenerationMode } from "../../types/studio";

type StudioContextValue = {
  meta: Meta;
  voices: Voice[];
  statuses: ModelStatus[];
  providers: TranslationProvider[];
  settings: AppSettings | null;
  setSettings: (settings: AppSettings) => void;
  history: HistoryEntry[];
  busy: boolean;
  message: string;
  error: string | null;
  installedCount: number;
  refreshAll: () => Promise<void>;
  mode: GenerationMode;
  setMode: (mode: GenerationMode) => void;
  speechText: string;
  setSpeechText: (text: string) => void;
  selectedVoice: string;
  setSelectedVoice: (voice: string) => void;
  language: string;
  setLanguage: (language: string) => void;
  effectPreset: "raw" | "normalize" | "broadcast";
  setEffectPreset: (preset: "raw" | "normalize" | "broadcast") => void;
  instructs: string[];
  setInstructs: (items: string[]) => void;
  numStep: number;
  setNumStep: (value: number) => void;
  guidanceScale: number;
  setGuidanceScale: (value: number) => void;
  speed: number;
  setSpeed: (value: number) => void;
  duration: string;
  setDuration: (value: string) => void;
  denoise: boolean;
  setDenoise: (value: boolean) => void;
  preprocessPrompt: boolean;
  setPreprocessPrompt: (value: boolean) => void;
  postprocessOutput: boolean;
  setPostprocessOutput: (value: boolean) => void;
  refAudio: File | null;
  setRefAudio: (file: File | null) => void;
  refText: string;
  setRefText: (text: string) => void;
  audioUrl: string | null;
  lastAudio: Blob | null;
  generateSpeech: () => Promise<void>;
  transcribeFile: File | null;
  setTranscribeFile: (file: File | null) => void;
  asrModel: string;
  setAsrModel: (model: string) => void;
  transcribeFormat: string;
  setTranscribeFormat: (format: string) => void;
  transcription: string;
  transcribe: () => Promise<void>;
  translateText: string;
  setTranslateText: (text: string) => void;
  translatedText: string;
  sourceLanguage: string;
  setSourceLanguage: (language: string) => void;
  targetLanguage: string;
  setTargetLanguage: (language: string) => void;
  provider: string;
  setProvider: (provider: string) => void;
  translate: () => Promise<void>;
  newVoiceId: string;
  setNewVoiceId: (id: string) => void;
  newVoiceFile: File | null;
  setNewVoiceFile: (file: File | null) => void;
  newVoiceText: string;
  setNewVoiceText: (text: string) => void;
  createVoice: () => Promise<void>;
  saveSettings: () => Promise<void>;
};

const StudioContext = createContext<StudioContextValue | null>(null);

export function StudioProvider({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<Meta>(emptyMeta);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [statuses, setStatuses] = useState<ModelStatus[]>([]);
  const [providers, setProviders] = useState<TranslationProvider[]>([]);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Ready.");
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [lastAudio, setLastAudio] = useState<Blob | null>(null);

  const [mode, setMode] = useState<GenerationMode>("speaker");
  const [speechText, setSpeechText] = useState("Xin chao, day la ban clone giong tu OmniVoice Kit.");
  const [selectedVoice, setSelectedVoice] = useState("");
  const [language, setLanguage] = useState("vi");
  const [effectPreset, setEffectPreset] = useState<"raw" | "normalize" | "broadcast">("raw");
  const [instructs, setInstructs] = useState<string[]>([]);
  const [numStep, setNumStep] = useState(16);
  const [guidanceScale, setGuidanceScale] = useState(2);
  const [speed, setSpeed] = useState(1);
  const [duration, setDuration] = useState("");
  const [denoise, setDenoise] = useState(true);
  const [preprocessPrompt, setPreprocessPrompt] = useState(true);
  const [postprocessOutput, setPostprocessOutput] = useState(true);
  const [refAudio, setRefAudio] = useState<File | null>(null);
  const [refText, setRefText] = useState("");

  const [transcribeFile, setTranscribeFile] = useState<File | null>(null);
  const [asrModel, setAsrModel] = useState("");
  const [transcribeFormat, setTranscribeFormat] = useState("verbose_json");
  const [transcription, setTranscription] = useState("");

  const [translateText, setTranslateText] = useState("Hello, this is a local studio workflow.");
  const [translatedText, setTranslatedText] = useState("");
  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguage, setTargetLanguage] = useState("vi");
  const [provider, setProvider] = useState("passthrough");

  const [newVoiceId, setNewVoiceId] = useState("");
  const [newVoiceFile, setNewVoiceFile] = useState<File | null>(null);
  const [newVoiceText, setNewVoiceText] = useState("");

  const activeModel = settings?.default_model || meta.omnivoice_models[0]?.id || "k2-fsa/OmniVoice";
  const activeAsrModel = asrModel || meta.asr_models[0]?.id || "Systran/faster-whisper-large-v3";
  const installedCount = useMemo(() => statuses.filter((status) => status.installed).length, [statuses]);

  const refreshAll = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [metaData, voiceData, statusData, providerData, settingsData, historyData] = await Promise.all([
        apiJson<{ data?: Meta } | Meta>("/v1/meta"),
        apiJson<{ data: Voice[] }>("/v1/voices"),
        apiJson<{ data: ModelStatus[] }>("/v1/model-status"),
        apiJson<{ data: TranslationProvider[] }>("/v1/translation/providers"),
        apiJson<{ data: AppSettings }>("/v1/settings"),
        apiJson<{ data: HistoryEntry[] }>("/v1/generation-history?limit=20"),
      ]);
      const nextMeta = "data" in metaData && metaData.data ? metaData.data : (metaData as Meta);
      setMeta(nextMeta);
      if (!asrModel && nextMeta.asr_models[0]?.id) {
        setAsrModel(nextMeta.asr_models[0].id);
      }
      setVoices(voiceData.data);
      setStatuses(statusData.data);
      setProviders(providerData.data);
      setSettings(settingsData.data);
      setProvider(settingsData.data.default_translation_provider || "passthrough");
      setEffectPreset(settingsData.data.default_effect_preset);
      setHistory(historyData.data);
      setMessage("Workspace synchronized with API.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }, [asrModel]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (!selectedVoice && voices.length > 0) {
      setSelectedVoice(voices[0].id);
    }
  }, [selectedVoice, voices]);

  async function generateSpeech() {
    setBusy(true);
    setError(null);
    try {
      let blob: Blob;
      if (mode === "speaker") {
        blob = await apiAudio("/v1/audio/speech", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(baseGenerationPayload({ voice: selectedVoice })),
        });
      } else if (mode === "clone") {
        if (!refAudio) throw new Error("Choose a reference audio file first.");
        const form = new FormData();
        form.set("text", speechText);
        form.set("ref_audio", refAudio);
        form.set("model", activeModel);
        form.set("ref_text", refText);
        form.set("language", language);
        form.set("instruct_items", JSON.stringify(instructs));
        form.set("num_step", String(numStep));
        form.set("guidance_scale", String(guidanceScale));
        form.set("speed", String(speed));
        if (duration) form.set("duration", duration);
        form.set("denoise", String(denoise));
        form.set("preprocess_prompt", String(preprocessPrompt));
        form.set("postprocess_output", String(postprocessOutput));
        form.set("effect_preset", effectPreset);
        blob = await apiAudio("/v1/audio/speech/clone", { method: "POST", body: form });
      } else {
        blob = await apiAudio("/v1/audio/speech/design", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(baseGenerationPayload({ instruct_items: instructs })),
        });
      }
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(blob));
      setLastAudio(blob);
      setMessage("Generated speech.wav.");
      await refreshHistoryOnly();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function baseGenerationPayload(extra: Record<string, unknown> = {}) {
    return {
      model: activeModel,
      input: speechText,
      language,
      instruct_items: instructs,
      num_step: numStep,
      guidance_scale: guidanceScale,
      speed,
      duration: duration ? Number(duration) : null,
      denoise,
      preprocess_prompt: preprocessPrompt,
      postprocess_output: postprocessOutput,
      effect_preset: effectPreset,
      ...extra,
    };
  }

  async function transcribe() {
    if (!transcribeFile) {
      setError("Choose an audio or video file first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("file", transcribeFile);
      form.set("model", activeAsrModel);
      form.set("language", language);
      form.set("response_format", transcribeFormat);
      const response = await fetch(`${API_BASE_URL}/v1/audio/transcriptions`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await response.text());
      const contentType = response.headers.get("content-type") || "";
      const output = contentType.includes("application/json")
        ? JSON.stringify(await response.json(), null, 2)
        : await response.text();
      setTranscription(output);
      setMessage("Transcription complete.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function translate() {
    setBusy(true);
    setError(null);
    try {
      const result = await apiJson<{ data: { text: string } }>("/v1/translation/translate", {
        method: "POST",
        body: JSON.stringify({
          text: translateText,
          source_language: sourceLanguage,
          target_language: targetLanguage,
          provider,
        }),
      });
      setTranslatedText(result.data.text);
      setMessage("Translation complete.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function createVoice() {
    if (!newVoiceId.trim() || !newVoiceFile) {
      setError("Provide speaker id and reference audio.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("speaker_id", newVoiceId.trim());
      form.set("ref_audio", newVoiceFile);
      form.set("ref_text", newVoiceText);
      form.set("language", language);
      await apiForm("/v1/voices", form);
      setNewVoiceId("");
      setNewVoiceFile(null);
      setNewVoiceText("");
      setMessage("Voice profile created.");
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function saveSettings() {
    if (!settings) return;
    setBusy(true);
    setError(null);
    try {
      const saved = await apiJson<{ data: AppSettings }>("/v1/settings", {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      setSettings(saved.data);
      setMessage("Settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function refreshHistoryOnly() {
    const result = await apiJson<{ data: HistoryEntry[] }>("/v1/generation-history?limit=20");
    setHistory(result.data);
  }

  return (
    <StudioContext.Provider
      value={{
        meta,
        voices,
        statuses,
        providers,
        settings,
        setSettings,
        history,
        busy,
        message,
        error,
        installedCount,
        refreshAll,
        mode,
        setMode,
        speechText,
        setSpeechText,
        selectedVoice,
        setSelectedVoice,
        language,
        setLanguage,
        effectPreset,
        setEffectPreset,
        instructs,
        setInstructs,
        numStep,
        setNumStep,
        guidanceScale,
        setGuidanceScale,
        speed,
        setSpeed,
        duration,
        setDuration,
        denoise,
        setDenoise,
        preprocessPrompt,
        setPreprocessPrompt,
        postprocessOutput,
        setPostprocessOutput,
        refAudio,
        setRefAudio,
        refText,
        setRefText,
        audioUrl,
        lastAudio,
        generateSpeech,
        transcribeFile,
        setTranscribeFile,
        asrModel,
        setAsrModel,
        transcribeFormat,
        setTranscribeFormat,
        transcription,
        transcribe,
        translateText,
        setTranslateText,
        translatedText,
        sourceLanguage,
        setSourceLanguage,
        targetLanguage,
        setTargetLanguage,
        provider,
        setProvider,
        translate,
        newVoiceId,
        setNewVoiceId,
        newVoiceFile,
        setNewVoiceFile,
        newVoiceText,
        setNewVoiceText,
        createVoice,
        saveSettings,
      }}
    >
      {children}
    </StudioContext.Provider>
  );
}

export function useStudio() {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error("useStudio must be used inside StudioProvider.");
  }
  return context;
}
