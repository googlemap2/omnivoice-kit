import React from "react";
import { Zap, Captions, Loader2, Upload, Volume2 } from "lucide-react";
import {
  type WhisperTranscriptionProgress,
  type CaptionAnimationStyle,
  type Subtitle,
  CAPTION_ANIMATION_STYLES,
  getAnimationStyleDisplayName,
} from "@openreel/core";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@openreel/ui";
import { AutoReframeSection } from "../";
import { AutoEditPanel } from "../../panels/AutoEditPanel";
import { HighlightExtractorPanel } from "../../panels/HighlightExtractorPanel";
import { InspectorSection } from "../shell/InspectorSection";
import { AudioResult } from "../AudioResult";
import { useProjectStore } from "../../../../stores/project-store";
import { toast } from "../../../../stores/notification-store";
import type {
  OmniVoiceProviderModel,
  OmniVoiceTranslationProvider,
} from "../../../../services/omnivoice-transcription";
import {
  fetchOmniVoiceVoices,
  generateOmniVoiceSpeech,
  type OmniVoiceVoice,
} from "../../../../services/omnivoice-transcription";

const TRANSCRIPT_LANGUAGES = [
  { value: "auto", label: "Auto detect" },
  { value: "vi", label: "Vietnamese" },
  { value: "en", label: "English" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "zh", label: "Chinese" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "es", label: "Spanish" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "th", label: "Thai" },
  { value: "id", label: "Indonesian" },
  { value: "ru", label: "Russian" },
];

const TARGET_LANGUAGES = [
  { value: "none", label: "No translation" },
  { value: "vi", label: "Vietnamese" },
  { value: "en", label: "English" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "zh", label: "Chinese" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "es", label: "Spanish" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "th", label: "Thai" },
  { value: "id", label: "Indonesian" },
  { value: "ru", label: "Russian" },
];

export interface AiTabProps {
  clipId: string;
  clipType: string | null;
  showVideoControls: boolean;
  showAudioEffects: boolean;
  showVideoEffects: boolean;
  transcriptionProgress: WhisperTranscriptionProgress | null;
  isTranscribing: boolean;
  transcriptLanguage: string;
  setTranscriptLanguage: React.Dispatch<React.SetStateAction<string>>;
  targetLanguage: string;
  setTargetLanguage: React.Dispatch<React.SetStateAction<string>>;
  translationEngine: "translation-provider" | "model-provider";
  setTranslationEngine: React.Dispatch<
    React.SetStateAction<"translation-provider" | "model-provider">
  >;
  translationProvider: string;
  setTranslationProvider: React.Dispatch<React.SetStateAction<string>>;
  providerModelId: string;
  setProviderModelId: React.Dispatch<React.SetStateAction<string>>;
  providerModelName: string;
  setProviderModelName: React.Dispatch<React.SetStateAction<string>>;
  translationProviders: OmniVoiceTranslationProvider[];
  providerModels: OmniVoiceProviderModel[];
  defaultAnimationStyle: CaptionAnimationStyle;
  setDefaultAnimationStyle: React.Dispatch<
    React.SetStateAction<CaptionAnimationStyle>
  >;
  handleGenerateSubtitles: (options?: {
    onTranscriptText?: (text: string, subtitles: Subtitle[]) => Promise<void> | void;
  }) => Promise<void>;
  handleSRTImport: (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => Promise<void>;
  srtInputRef: React.RefObject<HTMLInputElement>;
  handleRemoveBackground: () => void;
  handleEnhanceAudio: () => Promise<void>;
  handleAutoColor: () => Promise<void>;
  isEnhancingAudio: boolean;
  audioEnhanced: boolean;
  isApplyingSelectedClipEffect: boolean;
}

export const AiTab: React.FC<AiTabProps> = ({
  clipId,
  clipType,
  showVideoControls,
  showAudioEffects,
  showVideoEffects,
  transcriptionProgress,
  isTranscribing,
  transcriptLanguage,
  setTranscriptLanguage,
  targetLanguage,
  setTargetLanguage,
  translationEngine,
  setTranslationEngine,
  translationProvider,
  setTranslationProvider,
  providerModelId,
  setProviderModelId,
  providerModelName,
  setProviderModelName,
  translationProviders,
  providerModels,
  defaultAnimationStyle,
  setDefaultAnimationStyle,
  handleGenerateSubtitles,
  handleSRTImport,
  srtInputRef,
  handleRemoveBackground,
  handleEnhanceAudio,
  handleAutoColor,
  isEnhancingAudio,
  audioEnhanced,
  isApplyingSelectedClipEffect,
}) => {
  const importMedia = useProjectStore((state) => state.importMedia);
  const addClipToNewTrack = useProjectStore((state) => state.addClipToNewTrack);
  const addTrack = useProjectStore((state) => state.addTrack);
  const addClip = useProjectStore((state) => state.addClip);
  const renameTrack = useProjectStore((state) => state.renameTrack);
  const [ttsText, setTtsText] = React.useState("");
  const [synthesizeTranscriptAfterTranscription, setSynthesizeTranscriptAfterTranscription] =
    React.useState(false);
  const [mapTtsToTimelineAfterTranscription, setMapTtsToTimelineAfterTranscription] =
    React.useState(false);
  const [ttsLanguage, setTtsLanguage] = React.useState("auto");
  const [ttsVoiceId, setTtsVoiceId] = React.useState("");
  const [ttsSpeed, setTtsSpeed] = React.useState(1);
  const [ttsVoices, setTtsVoices] = React.useState<OmniVoiceVoice[]>([]);
  const [isLoadingTtsVoices, setIsLoadingTtsVoices] = React.useState(false);
  const [isGeneratingTts, setIsGeneratingTts] = React.useState(false);
  const [ttsAudio, setTtsAudio] = React.useState<Blob | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = React.useState<string | null>(null);
  const [isPlayingTts, setIsPlayingTts] = React.useState(false);
  const ttsAudioRef = React.useRef<HTMLAudioElement | null>(null);
  const selectedProviderModel = providerModels.find(
    (model) => model.id === providerModelId,
  );
  const providerModelNames = [
    ...(selectedProviderModel?.config?.available_models || []),
    selectedProviderModel?.config?.translation_model,
    selectedProviderModel?.config?.chat_model,
    selectedProviderModel?.transcription_model,
    selectedProviderModel?.speech_model,
  ].filter((model): model is string => Boolean(model && model.trim()));
  const selectedTtsVoice = ttsVoices.find((voice) => voice.id === ttsVoiceId);
  const selectedTtsVoiceName = selectedTtsVoice?.name || ttsVoiceId || "OmniVoice";

  React.useEffect(() => {
    let cancelled = false;

    setIsLoadingTtsVoices(true);
    fetchOmniVoiceVoices()
      .then((voices) => {
        if (cancelled) return;
        setTtsVoices(voices);
        setTtsVoiceId((current) => current || voices[0]?.id || "");
      })
      .catch((error) => {
        console.warn("[OmniVoice] Could not load voices:", error);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingTtsVoices(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    return () => {
      if (ttsAudioUrl) URL.revokeObjectURL(ttsAudioUrl);
    };
  }, [ttsAudioUrl]);

  const setGeneratedTtsAudio = React.useCallback(
    (blob: Blob) => {
      if (ttsAudioUrl) URL.revokeObjectURL(ttsAudioUrl);
      const nextUrl = URL.createObjectURL(blob);
      setTtsAudio(blob);
      setTtsAudioUrl(nextUrl);
      if (ttsAudioRef.current) {
        ttsAudioRef.current.src = nextUrl;
      }
    },
    [ttsAudioUrl],
  );

  const generateTtsFromText = React.useCallback(async (text: string) => {
    if (!text.trim() || !ttsVoiceId) return;
    setIsGeneratingTts(true);
    try {
      const blob = await generateOmniVoiceSpeech({
        text: text.trim(),
        voice: ttsVoiceId,
        language: ttsLanguage !== "auto" ? ttsLanguage : undefined,
        speed: ttsSpeed,
      });
      setGeneratedTtsAudio(blob);
      toast.success("OmniVoice TTS generated", "Audio is ready.");
    } catch (error) {
      toast.error(
        "OmniVoice TTS failed",
        error instanceof Error ? error.message : "Could not generate speech.",
      );
    } finally {
      setIsGeneratingTts(false);
    }
  }, [setGeneratedTtsAudio, ttsLanguage, ttsSpeed, ttsVoiceId]);

  const handleGenerateOmniVoiceTts = React.useCallback(async () => {
    await generateTtsFromText(ttsText);
  }, [generateTtsFromText, ttsText]);

  const handleGenerateTtsTimelineFromSubtitles = React.useCallback(
    async (subtitles: Subtitle[]) => {
      if (!ttsVoiceId || subtitles.length === 0) return;

      setIsGeneratingTts(true);
      try {
        const beforeTrackIds = new Set(
          useProjectStore.getState().project.timeline.tracks.map((track) => track.id),
        );
        const trackResult = await addTrack("audio");
        if (!trackResult.success) {
          throw new Error(String(trackResult.error || "Could not create audio track."));
        }

        const ttsTrack = useProjectStore
          .getState()
          .project.timeline.tracks.find(
            (track) => track.type === "audio" && !beforeTrackIds.has(track.id),
          );
        if (!ttsTrack) {
          throw new Error("Could not find OmniVoice TTS track.");
        }

        renameTrack(ttsTrack.id, "OmniVoice TTS");

        for (const [index, subtitle] of subtitles.entries()) {
          const text = subtitle.text.trim();
          if (!text) continue;

          const blob = await generateOmniVoiceSpeech({
            text,
            voice: ttsVoiceId,
            language: ttsLanguage !== "auto" ? ttsLanguage : undefined,
            speed: ttsSpeed,
          });
          const file = new File(
            [blob],
            `omnivoice_tts_${String(index + 1).padStart(3, "0")}.wav`,
            { type: "audio/wav" },
          );
          const mediaResult = await importMedia(file);
          if (!mediaResult.success || !mediaResult.actionId) {
            throw new Error(
              String(mediaResult.error || `Could not import TTS segment ${index + 1}.`),
            );
          }

          const clipResult = await addClip(
            ttsTrack.id,
            mediaResult.actionId,
            subtitle.startTime,
          );
          if (!clipResult.success) {
            throw new Error(
              String(clipResult.error || `Could not add TTS segment ${index + 1}.`),
            );
          }
        }

        toast.success(
          "OmniVoice TTS mapped",
          `Added ${subtitles.length} TTS segment${subtitles.length === 1 ? "" : "s"} to timeline.`,
        );
      } catch (error) {
        toast.error(
          "TTS timeline mapping failed",
          error instanceof Error ? error.message : "Could not map TTS to timeline.",
        );
      } finally {
        setIsGeneratingTts(false);
      }
    },
    [addClip, addTrack, importMedia, renameTrack, ttsLanguage, ttsSpeed, ttsVoiceId],
  );

  const handleGenerateTranscript = React.useCallback(async () => {
    await handleGenerateSubtitles({
      onTranscriptText: async (text, subtitles) => {
        setTtsText(text);
        if (mapTtsToTimelineAfterTranscription && ttsVoiceId) {
          await handleGenerateTtsTimelineFromSubtitles(subtitles);
          return;
        }
        if (synthesizeTranscriptAfterTranscription && ttsVoiceId) {
          await generateTtsFromText(text);
        }
      },
    });
  }, [
    generateTtsFromText,
    handleGenerateTtsTimelineFromSubtitles,
    handleGenerateSubtitles,
    mapTtsToTimelineAfterTranscription,
    synthesizeTranscriptAfterTranscription,
    ttsVoiceId,
  ]);

  const handleToggleTtsPlayback = React.useCallback(() => {
    if (!ttsAudioRef.current || !ttsAudioUrl) return;

    if (isPlayingTts) {
      ttsAudioRef.current.pause();
      setIsPlayingTts(false);
    } else {
      ttsAudioRef.current.play();
      setIsPlayingTts(true);
    }
  }, [isPlayingTts, ttsAudioUrl]);

  const ttsFileName = React.useCallback(
    () => `${selectedTtsVoiceName.replace(/[^\w-]+/g, "_")}_${Date.now()}.wav`,
    [selectedTtsVoiceName],
  );

  const handleSaveTtsToMedia = React.useCallback(async () => {
    if (!ttsAudio) return;
    const file = new File([ttsAudio], ttsFileName(), { type: "audio/wav" });
    const result = await importMedia(file);
    if (!result.success) {
      toast.error("Save failed", String(result.error || "Could not save audio."));
      return;
    }
    toast.success("Saved to Media", "OmniVoice audio was added to media assets.");
  }, [importMedia, ttsAudio, ttsFileName]);

  const handleAddTtsToTimeline = React.useCallback(async () => {
    if (!ttsAudio) return;
    const file = new File([ttsAudio], ttsFileName(), { type: "audio/wav" });
    const result = await importMedia(file);
    if (!result.success || !result.actionId) {
      toast.error("Timeline add failed", String(result.error || "Could not import audio."));
      return;
    }
    await addClipToNewTrack(result.actionId);
  }, [addClipToNewTrack, importMedia, ttsAudio, ttsFileName]);

  const handleDownloadTts = React.useCallback(() => {
    if (!ttsAudio) return;
    const url = URL.createObjectURL(ttsAudio);
    const link = document.createElement("a");
    link.href = url;
    link.download = ttsFileName();
    link.click();
    URL.revokeObjectURL(url);
  }, [ttsAudio, ttsFileName]);

  return (
    <>
      {clipType === "video" && (
        <>
          <InspectorSection
            title="OmniVoice Backend"
            sectionId="omnivoice-backend"
            defaultOpen={false}
          >
            <div className="space-y-3">
              <audio
                ref={ttsAudioRef}
                onEnded={() => setIsPlayingTts(false)}
                className="hidden"
              />
              <input
                ref={srtInputRef}
                type="file"
                accept=".srt,text/srt,text/plain"
                onChange={handleSRTImport}
                className="hidden"
              />
              <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <Captions size={14} className="text-primary" />
                  <span className="text-[11px] font-semibold text-primary">
                    Transcribe to captions
                  </span>
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide text-primary">
                    API
                  </span>
                </div>
                <p className="text-[10px] leading-4 text-text-muted">
                  Uses OmniVoice backend endpoint{" "}
                  <span className="font-mono text-text-secondary">
                    /v1/audio/transcriptions
                  </span>
                  .
                </p>
              </div>
              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  Transcript Language
                </label>
                <Select
                  value={transcriptLanguage}
                  onValueChange={setTranscriptLanguage}
                  disabled={isTranscribing}
                >
                  <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background-secondary border-border">
                    {TRANSCRIPT_LANGUAGES.map((language) => (
                      <SelectItem key={language.value} value={language.value}>
                        {language.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  Translate Captions
                </label>
                <Select
                  value={targetLanguage}
                  onValueChange={setTargetLanguage}
                  disabled={isTranscribing}
                >
                  <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                    <SelectValue placeholder="Original (no translation)" />
                  </SelectTrigger>
                  <SelectContent className="bg-background-secondary border-border">
                    {TARGET_LANGUAGES.map((language) => (
                      <SelectItem key={language.value} value={language.value}>
                        {language.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {targetLanguage !== "none" && (
                <>
                  <div>
                    <label className="text-[10px] text-text-secondary block mb-1">
                      Translation Engine
                    </label>
                    <Select
                      value={translationEngine}
                      onValueChange={(value) =>
                        setTranslationEngine(
                          value as "translation-provider" | "model-provider",
                        )
                      }
                      disabled={isTranscribing}
                    >
                      <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-background-secondary border-border">
                        <SelectItem value="translation-provider">
                          Translation Provider
                        </SelectItem>
                        <SelectItem value="model-provider">
                          Model Provider
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {translationEngine === "translation-provider" ? (
                    <div>
                      <label className="text-[10px] text-text-secondary block mb-1">
                        Translation Provider
                      </label>
                      <Select
                        value={translationProvider}
                        onValueChange={setTranslationProvider}
                        disabled={isTranscribing}
                      >
                        <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-background-secondary border-border">
                          <SelectItem value="default">
                            Backend default provider
                          </SelectItem>
                          {translationProviders.map((provider) => (
                            <SelectItem key={provider.id} value={provider.id}>
                              {provider.name || provider.id}
                              {provider.available === false ? " (unavailable)" : ""}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <>
                      <div>
                        <label className="text-[10px] text-text-secondary block mb-1">
                          Model Provider
                        </label>
                        <Select
                          value={providerModelId}
                          onValueChange={setProviderModelId}
                          disabled={isTranscribing}
                        >
                          <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-background-secondary border-border">
                            <SelectItem value="none">
                              Select model provider
                            </SelectItem>
                            {providerModels.map((provider) => (
                              <SelectItem key={provider.id} value={provider.id}>
                                {provider.provider_name || provider.id}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <label className="text-[10px] text-text-secondary block mb-1">
                          Provider Model
                        </label>
                        <Select
                          value={providerModelName}
                          onValueChange={setProviderModelName}
                          disabled={
                            isTranscribing || providerModelId === "none"
                          }
                        >
                          <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-background-secondary border-border">
                            <SelectItem value="auto">
                              Backend auto-select
                            </SelectItem>
                            {Array.from(new Set(providerModelNames)).map(
                              (modelName) => (
                                <SelectItem key={modelName} value={modelName}>
                                  {modelName}
                                </SelectItem>
                              ),
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}
                </>
              )}

              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  Caption Animation
                </label>
                <Select
                  value={defaultAnimationStyle}
                  onValueChange={(v) =>
                    setDefaultAnimationStyle(v as CaptionAnimationStyle)
                  }
                  disabled={isTranscribing}
                >
                  <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background-secondary border-border">
                    {CAPTION_ANIMATION_STYLES.map((style) => (
                      <SelectItem key={style} value={style}>
                        {getAnimationStyleDisplayName(style)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {transcriptionProgress ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Loader2
                      size={12}
                      className="animate-spin text-primary"
                    />
                    <span className="text-[10px] text-text-primary">
                      {transcriptionProgress.message}
                    </span>
                  </div>
                  <div className="h-1.5 bg-background-tertiary rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        transcriptionProgress.phase === "error"
                          ? "bg-red-500"
                          : transcriptionProgress.phase === "complete"
                            ? "bg-green-500"
                            : "bg-primary"
                      }`}
                      style={{ width: `${transcriptionProgress.progress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleGenerateTranscript}
                  disabled={
                    isTranscribing ||
                    isGeneratingTts ||
                    ((synthesizeTranscriptAfterTranscription ||
                      mapTtsToTimelineAfterTranscription) &&
                      !ttsVoiceId)
                  }
                  className="w-full py-2 bg-primary hover:bg-primary/80 text-black rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-2"
                >
                  <Captions size={14} />
                  Generate with OmniVoice
                </button>
              )}

              <div className="my-4 h-px bg-border" />

              <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <Volume2 size={14} className="text-primary" />
                  <span className="text-[11px] font-semibold text-primary">
                    Transcript text to speech
                  </span>
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide text-primary">
                    API
                  </span>
                </div>
                <p className="text-[10px] leading-4 text-text-muted">
                  Uses OmniVoice backend endpoint{" "}
                  <span className="font-mono text-text-secondary">
                    /v1/audio/speech
                  </span>
                  .
                </p>
              </div>

              <label className="flex items-start gap-2 rounded-lg border border-border bg-background-secondary p-2">
                <input
                  type="checkbox"
                  checked={synthesizeTranscriptAfterTranscription}
                  onChange={(event) => {
                    setSynthesizeTranscriptAfterTranscription(event.target.checked);
                    if (event.target.checked) {
                      setMapTtsToTimelineAfterTranscription(false);
                    }
                  }}
                  disabled={isTranscribing || isGeneratingTts}
                  className="mt-0.5"
                />
                <span>
                  <span className="block text-[10px] font-medium text-text-primary">
                    Generate TTS after transcription
                  </span>
                  <span className="block text-[9px] leading-4 text-text-muted">
                    The transcript/translated caption text will be sent to OmniVoice TTS automatically.
                  </span>
                </span>
              </label>

              <label className="flex items-start gap-2 rounded-lg border border-border bg-background-secondary p-2">
                <input
                  type="checkbox"
                  checked={mapTtsToTimelineAfterTranscription}
                  onChange={(event) => {
                    setMapTtsToTimelineAfterTranscription(event.target.checked);
                    if (event.target.checked) {
                      setSynthesizeTranscriptAfterTranscription(false);
                    }
                  }}
                  disabled={isTranscribing || isGeneratingTts}
                  className="mt-0.5"
                />
                <span>
                  <span className="block text-[10px] font-medium text-text-primary">
                    Map TTS to timeline by caption timing
                  </span>
                  <span className="block text-[9px] leading-4 text-text-muted">
                    Generates one TTS audio clip per caption and places each clip at its SRT start time.
                  </span>
                </span>
              </label>

              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  Voice
                </label>
                <Select
                  value={ttsVoiceId || "none"}
                  onValueChange={(value) => setTtsVoiceId(value === "none" ? "" : value)}
                  disabled={isGeneratingTts || isLoadingTtsVoices}
                >
                  <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                    <SelectValue placeholder="Select voice" />
                  </SelectTrigger>
                  <SelectContent className="bg-background-secondary border-border">
                    <SelectItem value="none">Select voice</SelectItem>
                    {ttsVoices.map((voice) => (
                      <SelectItem key={voice.id} value={voice.id}>
                        {voice.name || voice.id}
                        {voice.language ? ` · ${voice.language}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  TTS Language
                </label>
                <Select
                  value={ttsLanguage}
                  onValueChange={setTtsLanguage}
                  disabled={isGeneratingTts}
                >
                  <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-background-secondary border-border">
                    {TRANSCRIPT_LANGUAGES.map((language) => (
                      <SelectItem key={language.value} value={language.value}>
                        {language.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[10px] text-text-secondary">
                    Speed
                  </label>
                  <span className="text-[10px] text-text-muted">
                    {ttsSpeed.toFixed(1)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={ttsSpeed}
                  onChange={(event) => setTtsSpeed(Number(event.target.value))}
                  disabled={isGeneratingTts}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-[10px] text-text-secondary block mb-1">
                  Transcript / TTS Text
                </label>
                <textarea
                  value={ttsText}
                  onChange={(event) => setTtsText(event.target.value)}
                  placeholder="Transcript text will appear here after transcription, or enter text manually..."
                  className="w-full h-24 px-3 py-2 bg-background-secondary border border-border rounded-lg text-[11px] text-text-primary resize-none focus:outline-none focus:border-primary"
                />
              </div>

              <button
                onClick={handleGenerateOmniVoiceTts}
                disabled={isGeneratingTts || !ttsText.trim() || !ttsVoiceId}
                className="w-full py-2 bg-primary hover:bg-primary/80 text-black rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingTts ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Generating speech...
                  </>
                ) : (
                  <>
                    <Volume2 size={14} />
                    Generate Speech with OmniVoice
                  </>
                )}
              </button>

              {ttsAudio && (
                <AudioResult
                  generatedAudio={ttsAudio}
                  voiceName={selectedTtsVoiceName}
                  isPlaying={isPlayingTts}
                  isGenerating={isGeneratingTts}
                  onTogglePlayback={handleToggleTtsPlayback}
                  onSaveToMedia={handleSaveTtsToMedia}
                  onAddToTimeline={handleAddTtsToTimeline}
                  onDownload={handleDownloadTts}
                />
              )}
            </div>
          </InspectorSection>

          <InspectorSection
            title="Caption File Tools"
            sectionId="caption-file-tools"
            defaultOpen={false}
          >
            <div className="space-y-3">
              <button
                onClick={() => srtInputRef.current?.click()}
                disabled={isTranscribing}
                className="w-full py-2 bg-background-tertiary hover:bg-background-tertiary/80 border border-border text-text-primary rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Upload size={13} />
                Import SRT File
              </button>
              <p className="text-[10px] leading-4 text-text-muted">
                Local import only. This does not call OmniVoice backend.
              </p>
            </div>
          </InspectorSection>
        </>
      )}

      {clipType === "video" && (
        <InspectorSection
          title="Auto Reframe"
          sectionId="auto-reframe"
          defaultOpen={false}
        >
          <AutoReframeSection clipId={clipId} />
        </InspectorSection>
      )}

      {showAudioEffects && (
        <InspectorSection
          title="Beat-Synced Auto-Edit"
          sectionId="auto-edit"
          defaultOpen={false}
        >
          <AutoEditPanel onClose={() => {}} />
        </InspectorSection>
      )}

      {showAudioEffects && (
        <InspectorSection
          title="AI Highlights"
          sectionId="ai-highlights"
          defaultOpen={false}
        >
          <HighlightExtractorPanel clipId={clipId} />
        </InspectorSection>
      )}

      {(showVideoControls || showAudioEffects || showVideoEffects) && (
        <div className="border border-primary/30 bg-primary/5 rounded-xl p-4 relative overflow-hidden">
          <div className="flex items-center gap-2 text-primary mb-3">
            <Zap size={14} />
            <span className="text-xs font-bold">Quick Actions</span>
          </div>
          <div className="space-y-2">
            {showVideoControls && (
              <button
                onClick={handleRemoveBackground}
                disabled={isApplyingSelectedClipEffect}
                className={`w-full py-2 border rounded-lg text-[10px] transition-all ${
                  isApplyingSelectedClipEffect
                    ? "bg-background-tertiary border-border text-text-muted cursor-not-allowed"
                    : "bg-background-tertiary hover:bg-primary hover:text-white border-border hover:border-primary"
                }`}
              >
                Remove Background
              </button>
            )}
            {showAudioEffects && (
              <button
                onClick={handleEnhanceAudio}
                disabled={isEnhancingAudio || isApplyingSelectedClipEffect}
                className={`w-full py-2 border rounded-lg text-[10px] transition-all flex items-center justify-center gap-1.5 ${
                  audioEnhanced
                    ? "bg-green-500/20 border-green-500 text-green-400"
                    : isEnhancingAudio || isApplyingSelectedClipEffect
                      ? "bg-background-tertiary border-border text-text-muted cursor-not-allowed"
                      : "bg-background-tertiary hover:bg-primary hover:text-white border-border hover:border-primary"
                }`}
              >
                {isEnhancingAudio ? (
                  <>
                    <Loader2 size={12} className="animate-spin" />
                    Cleaning up...
                  </>
                ) : audioEnhanced ? (
                  "✓ Noise Reduced"
                ) : (
                  "Quick Dialogue Cleanup"
                )}
              </button>
            )}
            {showVideoEffects && (
              <button
                onClick={handleAutoColor}
                disabled={isApplyingSelectedClipEffect}
                className={`w-full py-2 border rounded-lg text-[10px] transition-all ${
                  isApplyingSelectedClipEffect
                    ? "bg-background-tertiary border-border text-text-muted cursor-not-allowed"
                    : "bg-background-tertiary hover:bg-primary hover:text-white border-border hover:border-primary"
                }`}
              >
                {isApplyingSelectedClipEffect ? "Applying..." : "Auto-Color"}
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
};
