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

const TTS_MODELS = [
  "kjanh/KhanhTTS-OmniVoice",
  "k2-fsa/OmniVoice",
];

const TTS_EFFECT_PRESETS = [
  { value: "raw", label: "Raw" },
  { value: "normalize", label: "Normalize" },
  { value: "broadcast", label: "Broadcast" },
] as const;

export interface OmnivoiceAiTabProps {
  clipId: string;
  clipType: string | null;
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
}

export const OmnivoiceAiTab: React.FC<OmnivoiceAiTabProps> = ({
  clipId,
  clipType,
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
}) => {
  const importMedia = useProjectStore((state) => state.importMedia);
  const replaceClipMediaAsset = useProjectStore((state) => state.replaceClipMediaAsset);
  const getClip = useProjectStore((state) => state.getClip);
  const updateClipMetadata = useProjectStore((state) => state.updateClipMetadata);
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
  const [ttsModel, setTtsModel] = React.useState(TTS_MODELS[0]);
  const [ttsEffectPreset, setTtsEffectPreset] = React.useState<
    "raw" | "normalize" | "broadcast"
  >("raw");
  const [ttsSpeed, setTtsSpeed] = React.useState(1);
  const [ttsVoices, setTtsVoices] = React.useState<OmniVoiceVoice[]>([]);
  const [isLoadingTtsVoices, setIsLoadingTtsVoices] = React.useState(false);
  const [isGeneratingTts, setIsGeneratingTts] = React.useState(false);
  const [ttsAudio, setTtsAudio] = React.useState<Blob | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = React.useState<string | null>(null);
  const [ttsAudioRequestKey, setTtsAudioRequestKey] = React.useState<string | null>(null);
  const [isPlayingTts, setIsPlayingTts] = React.useState(false);
  const ttsAudioRef = React.useRef<HTMLAudioElement | null>(null);
  const selectedProviderModel = providerModels.find(
    (model) => model.id === providerModelId,
  );
  const selectedAudioClip = clipType === "audio" ? getClip(clipId) : undefined;
  const selectedAudioTtsText =
    typeof selectedAudioClip?.metadata?.omnivoiceTtsText === "string"
      ? selectedAudioClip.metadata.omnivoiceTtsText
      : "";
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

  React.useEffect(() => {
    if (clipType !== "audio") return;
    setTtsText(selectedAudioTtsText);
  }, [clipId, clipType, selectedAudioTtsText]);

  const buildTtsRequestKey = React.useCallback(
    (text: string) =>
      JSON.stringify({
        text: text.trim(),
        voice: ttsVoiceId,
        model: ttsModel,
        language: ttsLanguage !== "auto" ? ttsLanguage : "",
        effectPreset: ttsEffectPreset,
        speed: ttsSpeed,
      }),
    [ttsEffectPreset, ttsLanguage, ttsModel, ttsSpeed, ttsVoiceId],
  );

  const setGeneratedTtsAudio = React.useCallback(
    (blob: Blob, requestKey: string) => {
      if (ttsAudioUrl) URL.revokeObjectURL(ttsAudioUrl);
      const nextUrl = URL.createObjectURL(blob);
      setTtsAudio(blob);
      setTtsAudioUrl(nextUrl);
      setTtsAudioRequestKey(requestKey);
      if (ttsAudioRef.current) {
        ttsAudioRef.current.src = nextUrl;
      }
    },
    [ttsAudioUrl],
  );

  const generateTtsFromText = React.useCallback(async (text: string) => {
    const normalizedText = text.trim();
    if (!normalizedText || !ttsVoiceId) return null;
    const requestKey = buildTtsRequestKey(normalizedText);
    setIsGeneratingTts(true);
    try {
      const blob = await generateOmniVoiceSpeech({
        text: normalizedText,
        voice: ttsVoiceId,
        model: ttsModel,
        language: ttsLanguage !== "auto" ? ttsLanguage : undefined,
        speed: ttsSpeed,
        effectPreset: ttsEffectPreset,
      });
      setGeneratedTtsAudio(blob, requestKey);
      toast.success("OmniVoice TTS generated", "Audio is ready.");
      return blob;
    } catch (error) {
      toast.error(
        "OmniVoice TTS failed",
        error instanceof Error ? error.message : "Could not generate speech.",
      );
      return null;
    } finally {
      setIsGeneratingTts(false);
    }
  }, [
    buildTtsRequestKey,
    setGeneratedTtsAudio,
    ttsEffectPreset,
    ttsLanguage,
    ttsModel,
    ttsSpeed,
    ttsVoiceId,
  ]);

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
            model: ttsModel,
            language: ttsLanguage !== "auto" ? ttsLanguage : undefined,
            speed: ttsSpeed,
            effectPreset: ttsEffectPreset,
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

          const addedClip = useProjectStore
            .getState()
            .project.timeline.tracks.find((track) => track.id === ttsTrack.id)
            ?.clips.find(
              (clip) =>
                clip.mediaId === mediaResult.actionId &&
                clip.startTime === subtitle.startTime,
            );
          if (addedClip) {
            updateClipMetadata(addedClip.id, {
              omnivoiceTtsText: text,
              omnivoiceTtsVoiceId: ttsVoiceId,
              omnivoiceTtsModel: ttsModel,
              omnivoiceTtsLanguage: ttsLanguage,
              omnivoiceTtsEffectPreset: ttsEffectPreset,
              omnivoiceTtsSpeed: ttsSpeed,
            });
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
    [
      addClip,
      addTrack,
      importMedia,
      renameTrack,
      ttsLanguage,
      ttsModel,
      ttsEffectPreset,
      ttsSpeed,
      ttsVoiceId,
      updateClipMetadata,
    ],
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
    const addedClip = useProjectStore
      .getState()
      .project.timeline.tracks.flatMap((track) => track.clips)
      .find((clip) => clip.mediaId === result.actionId);
    if (addedClip) {
      updateClipMetadata(addedClip.id, {
        omnivoiceTtsText: ttsText.trim(),
        omnivoiceTtsVoiceId: ttsVoiceId,
        omnivoiceTtsModel: ttsModel,
        omnivoiceTtsLanguage: ttsLanguage,
        omnivoiceTtsEffectPreset: ttsEffectPreset,
        omnivoiceTtsSpeed: ttsSpeed,
      });
    }
  }, [
    addClipToNewTrack,
    importMedia,
    ttsAudio,
    ttsFileName,
    ttsLanguage,
    ttsModel,
    ttsEffectPreset,
    ttsSpeed,
    ttsText,
    ttsVoiceId,
    updateClipMetadata,
  ]);

  const handleReplaceSelectedAudioWithTts = React.useCallback(async () => {
    const normalizedText = ttsText.trim();
    if (!selectedAudioClip || !normalizedText || !ttsVoiceId) return;

    setIsGeneratingTts(true);
    try {
      const requestKey = buildTtsRequestKey(normalizedText);
      let blob = ttsAudioRequestKey === requestKey ? ttsAudio : null;
      if (!blob) {
        blob = await generateOmniVoiceSpeech({
          text: normalizedText,
          voice: ttsVoiceId,
          model: ttsModel,
          language: ttsLanguage !== "auto" ? ttsLanguage : undefined,
          speed: ttsSpeed,
          effectPreset: ttsEffectPreset,
        });
        setGeneratedTtsAudio(blob, requestKey);
      }
      const file = new File([blob], ttsFileName(), { type: "audio/wav" });
      const result = await replaceClipMediaAsset(selectedAudioClip.id, file);
      if (!result.success) {
        throw new Error(String(result.error || "Could not replace selected audio."));
      }
      updateClipMetadata(selectedAudioClip.id, {
        omnivoiceTtsText: normalizedText,
        omnivoiceTtsVoiceId: ttsVoiceId,
        omnivoiceTtsModel: ttsModel,
        omnivoiceTtsLanguage: ttsLanguage,
        omnivoiceTtsEffectPreset: ttsEffectPreset,
        omnivoiceTtsSpeed: ttsSpeed,
      });
      toast.success(
        "Selected audio replaced",
        "The selected audio clip now uses the regenerated OmniVoice TTS.",
      );
    } catch (error) {
      toast.error(
        "Replace audio failed",
        error instanceof Error ? error.message : "Could not replace selected audio.",
      );
    } finally {
      setIsGeneratingTts(false);
    }
  }, [
    buildTtsRequestKey,
    replaceClipMediaAsset,
    selectedAudioClip,
    setGeneratedTtsAudio,
    ttsAudio,
    ttsAudioRequestKey,
    ttsFileName,
    ttsLanguage,
    ttsModel,
    ttsEffectPreset,
    ttsSpeed,
    ttsText,
    ttsVoiceId,
    updateClipMetadata,
  ]);

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
      {(clipType === "video" || clipType === "audio") && (
        <>
          <div className="mb-6 rounded-xl border border-primary/30 bg-primary/5 p-3">
            <div className="mb-4 flex items-start gap-2">
              <Zap size={15} className="mt-0.5 text-primary" />
              <div>
                <div className="text-xs font-bold text-primary">
                  OmniVoice Backend Tools
                </div>
                <p className="mt-1 text-[10px] leading-4 text-text-muted">
                  Server-backed transcription, translation, and TTS features.
                  These tools call OmniVoice backend APIs directly.
                </p>
              </div>
            </div>
          <InspectorSection
            title="Transcribe to captions"
            sectionId="omnivoice-backend"
            defaultOpen
          >
            <div className="space-y-3">
              <audio
                ref={ttsAudioRef}
                onEnded={() => setIsPlayingTts(false)}
                className="hidden"
              />
              {clipType === "video" && (
                <>
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
                </>
              )}
              {clipType === "video" && (
                <>
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

              {mapTtsToTimelineAfterTranscription && (
                <div className="space-y-3 rounded-lg border border-primary/30 bg-primary/5 p-3">
                  <div>
                    <label className="text-[10px] text-text-secondary block mb-1">
                      TTS Model
                    </label>
                    <Select
                      value={ttsModel}
                      onValueChange={setTtsModel}
                      disabled={isTranscribing || isGeneratingTts}
                    >
                      <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-background-secondary border-border">
                        {TTS_MODELS.map((model) => (
                          <SelectItem key={model} value={model}>
                            {model}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-[10px] text-text-secondary block mb-1">
                      TTS Voice
                    </label>
                    <Select
                      value={ttsVoiceId || "none"}
                      onValueChange={(value) =>
                        setTtsVoiceId(value === "none" ? "" : value)
                      }
                      disabled={
                        isTranscribing || isGeneratingTts || isLoadingTtsVoices
                      }
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
                      Effect Preset
                    </label>
                    <Select
                      value={ttsEffectPreset}
                      onValueChange={(value) =>
                        setTtsEffectPreset(
                          value as "raw" | "normalize" | "broadcast",
                        )
                      }
                      disabled={isTranscribing || isGeneratingTts}
                    >
                      <SelectTrigger className="w-full bg-background-secondary border-border text-text-primary text-[11px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-background-secondary border-border">
                        {TTS_EFFECT_PRESETS.map((preset) => (
                          <SelectItem key={preset.value} value={preset.value}>
                            {preset.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

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
                </>
              )}

            </div>
          </InspectorSection>

          <InspectorSection
            title="Transcript text to speech"
            sectionId="omnivoice-tts"
            defaultOpen={false}
          >
            <div className="space-y-3">
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
                    /v1/audio/speech/emotion-script
                  </span>
                  .
                </p>
              </div>

              {clipType === "video" && (
                <>
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

                </>
              )}

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
                    {clipType === "audio"
                      ? "Preview regenerated audio"
                      : "Generate Speech with OmniVoice"}
                  </>
                )}
              </button>

              {clipType === "audio" && selectedAudioClip && (
                <>
                  <button
                    onClick={handleReplaceSelectedAudioWithTts}
                    disabled={isGeneratingTts || !ttsText.trim() || !ttsVoiceId}
                    className="w-full py-2 bg-background-tertiary hover:bg-background-tertiary/80 border border-border text-text-primary rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Volume2 size={14} />
                    Replace selected audio with preview
                  </button>
                  <p className="text-[10px] leading-4 text-text-muted">
                    Preview first to verify voice. Replace uses the preview audio when
                    text, voice, language, and speed still match.
                  </p>
                </>
              )}

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
          </div>

          {clipType === "video" && (
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
          )}
        </>
      )}

    </>
  );
};
