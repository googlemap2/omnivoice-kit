"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  API_BASE_URL,
  type AppSettings,
  type DubbingResult,
  type Diagnostics,
  type HistoryEntry,
  type JobRecord,
  type Meta,
  type ModelStatus,
  type SubtitleSegment,
  type TranslationProvider,
  type Voice,
  apiAudio,
  apiForm,
  apiJson,
  apiWebSocketUrl,
  downloadBlob,
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
  jobs: JobRecord[];
  diagnostics: Diagnostics | null;
  logs: string[];
  busy: boolean;
  message: string;
  error: string | null;
  installedCount: number;
  refreshAll: () => Promise<void>;
  refreshJobs: () => Promise<void>;
  refreshDiagnostics: () => Promise<void>;
  clearLogs: () => Promise<void>;
  createTranslationJob: () => Promise<void>;
  cancelJob: (jobId: string) => Promise<void>;
  deleteJob: (jobId: string) => Promise<void>;
  downloadJobOutput: (job: JobRecord, artifact?: string) => Promise<void>;
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
  speechQueued: boolean;
  setSpeechQueued: (value: boolean) => void;
  transcribeFile: File | null;
  setTranscribeFile: (file: File | null) => void;
  asrModel: string;
  setAsrModel: (model: string) => void;
  transcribeFormat: string;
  setTranscribeFormat: (format: string) => void;
  transcription: string;
  setTranscription: (text: string) => void;
  transcribe: () => Promise<void>;
  transcribeQueued: boolean;
  setTranscribeQueued: (value: boolean) => void;
  transcribeTranslate: boolean;
  setTranscribeTranslate: (value: boolean) => void;
  dictationActive: boolean;
  dictationTranscript: string;
  startDictation: () => Promise<void>;
  stopDictation: () => void;
  subtitleFile: File | null;
  setSubtitleFile: (file: File | null) => void;
  subtitleFormat: string;
  setSubtitleFormat: (format: string) => void;
  subtitleSegments: SubtitleSegment[];
  setSubtitleSegments: (segments: SubtitleSegment[]) => void;
  updateSubtitleSegment: (index: number, patch: Partial<SubtitleSegment>) => void;
  addSubtitleSegment: () => void;
  deleteSubtitleSegment: (index: number) => void;
  importSubtitles: () => Promise<void>;
  exportSubtitles: () => Promise<void>;
  dubbingFile: File | null;
  setDubbingFile: (file: File | null) => void;
  dubbingFolderName: string;
  setDubbingFolderName: (name: string) => void;
  dubbingVoice: string;
  setDubbingVoice: (voice: string) => void;
  dubbingSourceLanguage: string;
  setDubbingSourceLanguage: (language: string) => void;
  dubbingTargetLanguage: string;
  setDubbingTargetLanguage: (language: string) => void;
  dubbingProvider: string;
  setDubbingProvider: (provider: string) => void;
  dubbingDiarize: boolean;
  setDubbingDiarize: (value: boolean) => void;
  dubbingSpeakerVoiceMap: Record<string, string>;
  setDubbingSpeakerVoice: (speaker: string, voice: string) => void;
  addDubbingSpeakerVoice: () => void;
  deleteDubbingSpeakerVoice: (speaker: string) => void;
  dubbingQueued: boolean;
  setDubbingQueued: (value: boolean) => void;
  dubbingResult: DubbingResult | null;
  dubbingAudioUrl: string | null;
  dubbingVideoUrl: string | null;
  runDubbing: () => Promise<void>;
  translateText: string;
  setTranslateText: (text: string) => void;
  translatedText: string;
  sourceLanguage: string;
  setSourceLanguage: (language: string) => void;
  targetLanguage: string;
  setTargetLanguage: (language: string) => void;
  provider: string;
  setProvider: (provider: string) => void;
  translateQueued: boolean;
  setTranslateQueued: (value: boolean) => void;
  translate: () => Promise<void>;
  newVoiceId: string;
  setNewVoiceId: (id: string) => void;
  newVoiceFile: File | null;
  setNewVoiceFile: (file: File | null) => void;
  newVoiceText: string;
  setNewVoiceText: (text: string) => void;
  createVoice: () => Promise<void>;
  updateVoiceProfile: (
    voiceId: string,
    updates: Partial<Pick<Voice, "name" | "language" | "tags" | "favorite" | "notes" | "preview_path">>,
  ) => Promise<void>;
  deleteVoiceProfile: (voiceId: string) => Promise<void>;
  generateVoicePreview: (voiceId: string) => Promise<void>;
  exportVoiceProfile: (voiceId: string) => Promise<void>;
  importVoicePackage: (file: File) => Promise<void>;
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
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Ready.");
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [lastAudio, setLastAudio] = useState<Blob | null>(null);
  const [speechQueued, setSpeechQueued] = useState(false);

  const [mode, setMode] = useState<GenerationMode>("emotion");
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
  const [transcribeQueued, setTranscribeQueued] = useState(false);
  const [transcribeTranslate, setTranscribeTranslate] = useState(false);
  const [dictationActive, setDictationActive] = useState(false);
  const [dictationTranscript, setDictationTranscript] = useState("");
  const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
  const [subtitleFormat, setSubtitleFormat] = useState("srt");
  const [subtitleSegments, setSubtitleSegments] = useState<SubtitleSegment[]>([]);
  const [dubbingFile, setDubbingFile] = useState<File | null>(null);
  const [dubbingFolderName, setDubbingFolderName] = useState("");
  const [dubbingVoice, setDubbingVoice] = useState("");
  const [dubbingSourceLanguage, setDubbingSourceLanguage] = useState("en");
  const [dubbingTargetLanguage, setDubbingTargetLanguage] = useState("vi");
  const [dubbingProvider, setDubbingProvider] = useState("passthrough");
  const [dubbingDiarize, setDubbingDiarize] = useState(false);
  const [dubbingSpeakerVoiceMap, setDubbingSpeakerVoiceMap] = useState<Record<string, string>>({});
  const [dubbingQueued, setDubbingQueued] = useState(false);
  const [dubbingResult, setDubbingResult] = useState<DubbingResult | null>(null);
  const [dubbingAudioUrl, setDubbingAudioUrl] = useState<string | null>(null);
  const [dubbingVideoUrl, setDubbingVideoUrl] = useState<string | null>(null);

  const [translateText, setTranslateText] = useState("Hello, this is a local studio workflow.");
  const [translatedText, setTranslatedText] = useState("");
  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguage, setTargetLanguage] = useState("vi");
  const [provider, setProvider] = useState("passthrough");
  const [translateQueued, setTranslateQueued] = useState(false);

  const [newVoiceId, setNewVoiceId] = useState("");
  const [newVoiceFile, setNewVoiceFile] = useState<File | null>(null);
  const [newVoiceText, setNewVoiceText] = useState("");
  const dictationSocketRef = useRef<WebSocket | null>(null);
  const dictationRecorderRef = useRef<MediaRecorder | null>(null);
  const dictationStreamRef = useRef<MediaStream | null>(null);

  const activeModel = settings?.default_model || meta.omnivoice_models[0]?.id || "k2-fsa/OmniVoice";
  const activeAsrModel = asrModel || meta.asr_models[0]?.id || "Systran/faster-whisper-large-v3";
  const installedCount = useMemo(() => statuses.filter((status) => status.installed).length, [statuses]);

  const refreshAll = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [metaData, voiceData, statusData, providerData, settingsData, historyData, jobsData] = await Promise.all([
        apiJson<{ data?: Meta } | Meta>("/v1/meta"),
        apiJson<{ data: Voice[] }>("/v1/voices"),
        apiJson<{ data: ModelStatus[] }>("/v1/model-status"),
        apiJson<{ data: TranslationProvider[] }>("/v1/translation/providers"),
        apiJson<{ data: AppSettings }>("/v1/settings"),
        apiJson<{ data: HistoryEntry[] }>("/v1/generation-history?limit=20"),
        apiJson<{ data: JobRecord[] }>("/v1/jobs?limit=50"),
      ]);
      const nextMeta = "data" in metaData && metaData.data ? metaData.data : (metaData as Meta);
      setMeta(nextMeta);
      if (!asrModel && nextMeta.asr_models[0]?.id) {
        setAsrModel(nextMeta.asr_models[0].id);
      }
      setVoices(voiceData.data.map(normalizeVoice));
      setStatuses(statusData.data);
      setProviders(providerData.data);
      setSettings(settingsData.data);
      setProvider(settingsData.data.default_translation_provider || "passthrough");
      setDubbingProvider(settingsData.data.default_translation_provider || "passthrough");
      setEffectPreset(settingsData.data.default_effect_preset);
      setHistory(historyData.data);
      setJobs(jobsData.data);
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
    if (!dubbingVoice && voices.length > 0) {
      setDubbingVoice(voices[0].id);
    }
  }, [dubbingVoice, selectedVoice, voices]);

  async function generateSpeech() {
    setBusy(true);
    setError(null);
    try {
      let blob: Blob;
      if (mode === "speaker") {
        const init = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(baseGenerationPayload({ voice: selectedVoice, queued: speechQueued })),
        };
        if (speechQueued) {
          const result = await apiJson<{ data: JobRecord }>("/v1/audio/speech", init);
          trackQueuedJob(result.data, "speech");
          return;
        }
        blob = await apiAudio("/v1/audio/speech", init);
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
        form.set("queued", String(speechQueued));
        if (speechQueued) {
          const result = await apiForm<{ data: JobRecord }>("/v1/audio/speech/clone", form);
          trackQueuedJob(result.data, "speech");
          return;
        }
        blob = await apiAudio("/v1/audio/speech/clone", { method: "POST", body: form });
      } else if (mode === "emotion") {
        const init = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            baseGenerationPayload({
              voice: selectedVoice,
              default_instruct: instructs.length > 0 ? instructs.join(", ") : null,
              gap_ms: 120,
              queued: speechQueued,
            }),
          ),
        };
        if (speechQueued) {
          const result = await apiJson<{ data: JobRecord }>("/v1/audio/speech/emotion-script", init);
          trackQueuedJob(result.data, "speech");
          return;
        }
        blob = await apiAudio("/v1/audio/speech/emotion-script", init);
      } else {
        const init = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(baseGenerationPayload({ instruct_items: instructs, queued: speechQueued })),
        };
        if (speechQueued) {
          const result = await apiJson<{ data: JobRecord }>("/v1/audio/speech/design", init);
          trackQueuedJob(result.data, "speech");
          return;
        }
        blob = await apiAudio("/v1/audio/speech/design", init);
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
      form.set("queued", String(transcribeQueued));
      form.set("translate", String(transcribeTranslate));
      if (transcribeTranslate) {
        form.set("source_language", sourceLanguage);
        form.set("target_language", targetLanguage);
        form.set("translation_provider", provider);
      }
      if (transcribeQueued) {
        const result = await apiForm<{ data: JobRecord }>("/v1/audio/transcriptions", form);
        trackQueuedJob(result.data, "transcription");
        return;
      }
      const response = await fetch(`${API_BASE_URL}/v1/audio/transcriptions`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await response.text());
      const contentType = response.headers.get("content-type") || "";
      const output = contentType.includes("application/json")
        ? JSON.stringify(await handleTranscriptionJson(response), null, 2)
        : await response.text();
      setTranscription(output);
      setMessage("Transcription complete.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleTranscriptionJson(response: Response) {
    const data = await response.json();
    if (Array.isArray(data?.segments)) {
      setSubtitleSegments(normalizeSubtitleSegments(data.segments));
    }
    return data;
  }

  async function startDictation() {
    if (dictationActive) return;
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("This browser does not support microphone dictation.");
      return;
    }
    setError(null);
    setMessage("Starting dictation...");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const params = new URLSearchParams({
        model: activeAsrModel,
        language,
      });
      const socket = new WebSocket(apiWebSocketUrl(`/v1/dictation/ws?${params.toString()}`));
      dictationStreamRef.current = stream;
      dictationRecorderRef.current = recorder;
      dictationSocketRef.current = socket;
      setDictationActive(true);
      setMessage("Connecting dictation WebSocket...");

      socket.onopen = () => {
        socket.send(JSON.stringify({ type: "start", mime_type: recorder.mimeType }));
        recorder.start(1000);
        setMessage("Dictation recording.");
      };
      socket.onmessage = (event) => {
        const payload = parseDictationEvent(event.data);
        if (payload.type === "partial" && typeof payload.bytes_received === "number") {
          setMessage(`Dictation received ${payload.bytes_received} bytes.`);
        } else if (payload.type === "final") {
          const text = typeof payload.text === "string" ? payload.text : "";
          setDictationTranscript(text);
          setTranscription(text);
          setMessage("Dictation complete.");
        } else if (payload.type === "error") {
          setError(typeof payload.message === "string" ? payload.message : "Dictation failed.");
        }
      };
      socket.onerror = () => {
        setError("Dictation WebSocket failed.");
        cleanupDictation(false);
      };
      socket.onclose = () => {
        cleanupDictation(false);
      };
      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
          socket.send(await event.data.arrayBuffer());
        }
      };
      recorder.onerror = () => {
        setError("Microphone recorder failed.");
        stopDictation();
      };
    } catch (err) {
      cleanupDictation(true);
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function stopDictation() {
    const recorder = dictationRecorderRef.current;
    const socket = dictationSocketRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      setTimeout(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "stop" }));
        }
      }, 150);
    } else {
      cleanupDictation(true);
    }
    setMessage("Stopping dictation...");
  }

  function cleanupDictation(closeSocket: boolean) {
    dictationStreamRef.current?.getTracks().forEach((track) => track.stop());
    dictationStreamRef.current = null;
    dictationRecorderRef.current = null;
    if (closeSocket) {
      dictationSocketRef.current?.close();
    }
    dictationSocketRef.current = null;
    setDictationActive(false);
  }

  function parseDictationEvent(data: unknown): Record<string, unknown> {
    if (typeof data !== "string") return {};
    try {
      const parsed = JSON.parse(data);
      return typeof parsed === "object" && parsed !== null ? (parsed as Record<string, unknown>) : {};
    } catch {
      return {};
    }
  }

  async function importSubtitles() {
    if (!subtitleFile) {
      setError("Choose a subtitle file first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("file", subtitleFile);
      form.set("format", subtitleFormat);
      const result = await apiForm<{ data: Array<Record<string, unknown>>; format: string }>("/v1/subtitles/import", form);
      setSubtitleFormat(result.format);
      const segments = normalizeSubtitleSegments(result.data);
      setSubtitleSegments(segments);
      setTranscription(JSON.stringify({ segments }, null, 2));
      setMessage("Subtitle import complete.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function exportSubtitles() {
    setBusy(true);
    setError(null);
    try {
      let segments: unknown = subtitleSegments;
      if (subtitleSegments.length === 0) {
        const parsed = JSON.parse(transcription);
        segments = Array.isArray(parsed) ? parsed : parsed.segments;
      }
      if (!Array.isArray(segments)) {
        throw new Error("Subtitle editor must contain at least one segment.");
      }
      const translatedBlob = await apiAudio("/v1/subtitles/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format: subtitleFormat, segments }),
      });
      downloadBlob(translatedBlob, `subtitles.translated.${subtitleFormat}`);

      const rawSegments = segments
        .map((segment) => {
          if (typeof segment !== "object" || segment === null) return segment;
          const item = segment as SubtitleSegment;
          const sourceText = typeof item.metadata?.source_text === "string" ? item.metadata.source_text : null;
          return sourceText ? { ...item, text: sourceText } : item;
        });
      const hasRawSource = rawSegments.some((segment, index) => {
        if (typeof segment !== "object" || segment === null) return false;
        const original = segments[index] as SubtitleSegment | undefined;
        return Boolean(original?.metadata?.source_text);
      });
      if (hasRawSource) {
        const rawBlob = await apiAudio("/v1/subtitles/export", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ format: subtitleFormat, segments: rawSegments }),
        });
        downloadBlob(rawBlob, `subtitles.raw.${subtitleFormat}`);
        setMessage(`Exported raw and translated subtitles.${subtitleFormat}.`);
      } else {
        setMessage(`Exported subtitles.translated.${subtitleFormat}.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runDubbing() {
    if (!dubbingFile) {
      setError("Choose an audio or video file first.");
      return;
    }
    if (!dubbingVoice) {
      setError("Choose a voice profile first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setMessage(dubbingQueued ? "Submitting dubbing job to queue..." : "Dubbing media synchronously. Waiting for API response...");
      const form = new FormData();
      form.set("file", dubbingFile);
      form.set("folder_name", dubbingFolderName);
      form.set("voice", dubbingVoice);
      form.set("source_language", dubbingSourceLanguage);
      form.set("target_language", dubbingTargetLanguage);
      form.set("translation_provider", dubbingProvider);
      form.set("tts_model", activeModel);
      form.set("asr_model", activeAsrModel);
      form.set("effect_preset", effectPreset);
      form.set("num_step", String(numStep));
      form.set("guidance_scale", String(guidanceScale));
      form.set("speed", String(speed));
      form.set("enable_diarization", String(dubbingDiarize));
      form.set("speaker_voice_map", JSON.stringify(dubbingSpeakerVoiceMap));
      form.set("queued", String(dubbingQueued));
      const result = await apiForm<{ object: string; data: DubbingResult | JobRecord }>("/v1/dubbing/dub-upload", form);
      if (result.object === "job") {
        const job = result.data as JobRecord;
        setDubbingResult(null);
        if (dubbingAudioUrl) URL.revokeObjectURL(dubbingAudioUrl);
        if (dubbingVideoUrl) URL.revokeObjectURL(dubbingVideoUrl);
        setDubbingAudioUrl(null);
        setDubbingVideoUrl(null);
        trackQueuedJob(job, "dubbing");
        await refreshJobs();
      } else {
        const dubbing = result.data as DubbingResult;
        setDubbingResult(dubbing);
        await loadDubbingMedia(dubbing);
        setMessage(`Dubbing complete: ${dubbing.segment_count} segments.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function loadDubbingMedia(result: DubbingResult) {
    if (dubbingAudioUrl) URL.revokeObjectURL(dubbingAudioUrl);
    if (dubbingVideoUrl) URL.revokeObjectURL(dubbingVideoUrl);

    const audioBlob = await apiAudio(`/v1/files?path=${encodeURIComponent(result.dubbed_audio_path)}`);
    setDubbingAudioUrl(URL.createObjectURL(audioBlob));

    if (result.dubbed_video_path) {
      const videoBlob = await apiAudio(`/v1/files?path=${encodeURIComponent(result.dubbed_video_path)}`);
      setDubbingVideoUrl(URL.createObjectURL(videoBlob));
    } else {
      setDubbingVideoUrl(null);
    }
  }

  function updateSubtitleSegment(index: number, patch: Partial<SubtitleSegment>) {
    setSubtitleSegments((current) => {
      const next = current.map((segment, itemIndex) => (itemIndex === index ? { ...segment, ...patch } : segment));
      setTranscription(JSON.stringify({ segments: next }, null, 2));
      return next;
    });
  }

  function addSubtitleSegment() {
    setSubtitleSegments((current) => {
      const previous = current[current.length - 1];
      const start = previous ? Number(previous.end.toFixed(3)) : 0;
      const nextSegment: SubtitleSegment = {
        id: current.length,
        start,
        end: Number((start + 2).toFixed(3)),
        text: "",
        speaker: null,
        metadata: {},
      };
      const next = [...current, nextSegment];
      setTranscription(JSON.stringify({ segments: next }, null, 2));
      return next;
    });
  }

  function deleteSubtitleSegment(index: number) {
    setSubtitleSegments((current) => {
      const next = current
        .filter((_, itemIndex) => itemIndex !== index)
        .map((segment, itemIndex) => ({ ...segment, id: itemIndex }));
      setTranscription(JSON.stringify({ segments: next }, null, 2));
      return next;
    });
  }

  function normalizeSubtitleSegments(items: Array<Record<string, unknown>>): SubtitleSegment[] {
    return items.map((item, index) => ({
      id: Number(item.id ?? index),
      start: Number(item.start ?? 0),
      end: Number(item.end ?? item.start ?? 0),
      text: String(item.text ?? ""),
      speaker: item.speaker ? String(item.speaker) : null,
      metadata: typeof item.metadata === "object" && item.metadata !== null ? (item.metadata as Record<string, unknown>) : {},
    }));
  }

  function setDubbingSpeakerVoice(speaker: string, voice: string) {
    setDubbingSpeakerVoiceMap((current) => {
      const normalizedSpeaker = speaker.trim();
      if (!normalizedSpeaker) return current;
      return { ...current, [normalizedSpeaker]: voice };
    });
  }

  function addDubbingSpeakerVoice() {
    setDubbingSpeakerVoiceMap((current) => {
      for (let index = 0; index < 20; index += 1) {
        const speaker = `SPEAKER_${String(index).padStart(2, "0")}`;
        if (!(speaker in current)) {
          return { ...current, [speaker]: dubbingVoice || selectedVoice || voices[0]?.id || "" };
        }
      }
      return current;
    });
  }

  function deleteDubbingSpeakerVoice(speaker: string) {
    setDubbingSpeakerVoiceMap((current) => {
      const next = { ...current };
      delete next[speaker];
      return next;
    });
  }

  async function translate() {
    setBusy(true);
    setError(null);
    try {
      if (translateQueued) {
        const result = await apiJson<{ data: JobRecord }>("/v1/jobs", {
          method: "POST",
          body: JSON.stringify({
            type: "translation",
            params: {
              text: translateText,
              source_language: sourceLanguage,
              target_language: targetLanguage,
              provider,
            },
          }),
        });
        trackQueuedJob(result.data, "translation");
        return;
      }
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
      await apiForm("/v1/voice-profiles", form);
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

  async function updateVoiceProfile(
    voiceId: string,
    updates: Partial<Pick<Voice, "name" | "language" | "tags" | "favorite" | "notes" | "preview_path">>,
  ) {
    setBusy(true);
    setError(null);
    try {
      await apiJson<{ data: Voice }>(`/v1/voice-profiles/${encodeURIComponent(voiceId)}`, {
        method: "PATCH",
        body: JSON.stringify(updates),
      });
      setMessage("Voice profile updated.");
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function deleteVoiceProfile(voiceId: string) {
    setBusy(true);
    setError(null);
    try {
      await apiJson(`/v1/voice-profiles/${encodeURIComponent(voiceId)}`, {
        method: "DELETE",
      });
      if (selectedVoice === voiceId) setSelectedVoice("");
      if (dubbingVoice === voiceId) setDubbingVoice("");
      setMessage("Voice profile deleted.");
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function generateVoicePreview(voiceId: string) {
    setBusy(true);
    setError(null);
    try {
      await apiJson<{ data: Voice }>(`/v1/voice-profiles/${encodeURIComponent(voiceId)}/preview`, {
        method: "POST",
        body: JSON.stringify({
          text: speechText || undefined,
          language,
          effect_preset: effectPreset,
          num_step: numStep,
          guidance_scale: guidanceScale,
          speed,
        }),
      });
      setMessage("Voice preview generated.");
      await refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function exportVoiceProfile(voiceId: string) {
    setBusy(true);
    setError(null);
    try {
      const blob = await apiAudio(`/v1/voice-profiles/${encodeURIComponent(voiceId)}/package`);
      downloadBlob(blob, `${voiceId}.voicepkg.zip`);
      setMessage("Voice package exported.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function importVoicePackage(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("file", file);
      await apiForm<{ data: Voice }>("/v1/voice-profiles/import-package", form);
      setMessage("Voice package imported.");
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

  function trackQueuedJob(job: JobRecord, label: string) {
    setJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
    setMessage(`Queued ${label} job ${job.id}.`);
  }

  async function refreshDiagnostics() {
    setBusy(true);
    setError(null);
    try {
      const [diagnosticsResult, logsResult] = await Promise.all([
        apiJson<{ data: Diagnostics }>("/v1/diagnostics"),
        apiJson<{ data: string[] }>("/v1/logs?limit=200"),
      ]);
      setDiagnostics(diagnosticsResult.data);
      setLogs(logsResult.data);
      setMessage("Diagnostics refreshed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function clearLogs() {
    setBusy(true);
    setError(null);
    try {
      await apiJson("/v1/logs", { method: "DELETE" });
      setLogs([]);
      setMessage("Logs cleared.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function refreshJobs() {
    try {
      const result = await apiJson<{ data: JobRecord[] }>("/v1/jobs?limit=50");
      setJobs(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function createTranslationJob() {
    setBusy(true);
    setError(null);
    try {
      const result = await apiJson<{ data: JobRecord }>("/v1/jobs", {
        method: "POST",
        body: JSON.stringify({
          type: "translation",
          params: {
            text: translateText,
            source_language: sourceLanguage,
            target_language: targetLanguage,
            provider,
          },
        }),
      });
      setJobs((current) => [result.data, ...current.filter((job) => job.id !== result.data.id)]);
      setMessage(`Queued translation job ${result.data.id}.`);
      await refreshJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function cancelJob(jobId: string) {
    try {
      const result = await apiJson<{ data: JobRecord }>(`/v1/jobs/${jobId}/cancel`, { method: "POST" });
      setJobs((current) => current.map((job) => (job.id === jobId ? result.data : job)));
      setMessage(`Canceled job ${jobId}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function deleteJob(jobId: string) {
    try {
      await apiJson(`/v1/jobs/${jobId}`, { method: "DELETE" });
      setJobs((current) => current.filter((job) => job.id !== jobId));
      setMessage(`Deleted job ${jobId}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function downloadJobOutput(job: JobRecord, artifact = "primary") {
    try {
      const outputPath = jobOutputPath(job, artifact);
      let blob: Blob;
      let filename: string;
      if (outputPath) {
        blob = await apiAudio(`/v1/files?path=${encodeURIComponent(outputPath)}`);
        filename = outputPath.split(/[\\/]/).pop() || `${job.type}-${job.id}`;
      } else {
        const fallback = jobFallbackDownload(job, artifact);
        if (!fallback) throw new Error("Job has no downloadable output.");
        blob = fallback.blob;
        filename = fallback.filename;
      }
      downloadLocalBlob(blob, filename);
      setMessage(`Downloaded ${filename}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function jobOutputPath(job: JobRecord, artifact: string) {
    const result = job.result || {};
    if (artifact === "audio" && typeof result.dubbed_audio_path === "string") return result.dubbed_audio_path;
    if (artifact === "video" && typeof result.dubbed_video_path === "string") return result.dubbed_video_path;
    if (artifact === "srt" && typeof result.srt_path === "string") return result.srt_path;
    if (artifact === "vtt" && typeof result.vtt_path === "string") return result.vtt_path;
    if (artifact === "voices" && typeof result.voice_manifest_path === "string") return result.voice_manifest_path;
    if (typeof result.output_path === "string") return result.output_path;
    if (typeof result.dubbed_video_path === "string") return result.dubbed_video_path;
    if (typeof result.dubbed_audio_path === "string") return result.dubbed_audio_path;
    return "";
  }

  function jobFallbackDownload(job: JobRecord, artifact: string) {
    if (!job.result) return null;
    if (job.type === "translation" && typeof job.result.text === "string" && artifact !== "json") {
      return {
        blob: new Blob([job.result.text], { type: "text/plain;charset=utf-8" }),
        filename: `translation-${job.id.slice(0, 8)}.txt`,
      };
    }
    return {
      blob: new Blob([JSON.stringify(job.result, null, 2)], { type: "application/json" }),
      filename: `${job.type}-${job.id.slice(0, 8)}.json`,
    };
  }

  function downloadLocalBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
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
        jobs,
        diagnostics,
        logs,
        busy,
        message,
        error,
        installedCount,
        refreshAll,
        refreshJobs,
        refreshDiagnostics,
        clearLogs,
        createTranslationJob,
        cancelJob,
        deleteJob,
        downloadJobOutput,
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
        speechQueued,
        setSpeechQueued,
        transcribeFile,
        setTranscribeFile,
        asrModel,
        setAsrModel,
        transcribeFormat,
        setTranscribeFormat,
        transcription,
        setTranscription,
        transcribe,
        transcribeQueued,
        setTranscribeQueued,
        transcribeTranslate,
        setTranscribeTranslate,
        dictationActive,
        dictationTranscript,
        startDictation,
        stopDictation,
        subtitleFile,
        setSubtitleFile,
        subtitleFormat,
        setSubtitleFormat,
        subtitleSegments,
        setSubtitleSegments,
        updateSubtitleSegment,
        addSubtitleSegment,
        deleteSubtitleSegment,
        importSubtitles,
        exportSubtitles,
        dubbingFile,
        setDubbingFile,
        dubbingFolderName,
        setDubbingFolderName,
        dubbingVoice,
        setDubbingVoice,
        dubbingSourceLanguage,
        setDubbingSourceLanguage,
        dubbingTargetLanguage,
        setDubbingTargetLanguage,
        dubbingProvider,
        setDubbingProvider,
        dubbingDiarize,
        setDubbingDiarize,
        dubbingSpeakerVoiceMap,
        setDubbingSpeakerVoice,
        addDubbingSpeakerVoice,
        deleteDubbingSpeakerVoice,
        dubbingQueued,
        setDubbingQueued,
        dubbingResult,
        dubbingAudioUrl,
        dubbingVideoUrl,
        runDubbing,
        translateText,
        setTranslateText,
        translatedText,
        sourceLanguage,
        setSourceLanguage,
        targetLanguage,
        setTargetLanguage,
        provider,
        setProvider,
        translateQueued,
        setTranslateQueued,
        translate,
        newVoiceId,
        setNewVoiceId,
        newVoiceFile,
        setNewVoiceFile,
        newVoiceText,
        setNewVoiceText,
        createVoice,
        updateVoiceProfile,
        deleteVoiceProfile,
        generateVoicePreview,
        exportVoiceProfile,
        importVoicePackage,
        saveSettings,
      }}
    >
      {children}
    </StudioContext.Provider>
  );
}

function normalizeVoice(voice: Voice): Voice {
  return {
    ...voice,
    tags: Array.isArray(voice.tags) ? voice.tags : [],
    favorite: Boolean(voice.favorite),
    notes: voice.notes ?? null,
    preview_path: voice.preview_path ?? null,
    asset_dir: voice.asset_dir ?? null,
  };
}

export function useStudio() {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error("useStudio must be used inside StudioProvider.");
  }
  return context;
}
