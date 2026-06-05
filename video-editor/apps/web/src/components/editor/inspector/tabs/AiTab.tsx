import React from "react";
import { Zap, Captions, Loader2, Upload } from "lucide-react";
import {
  type WhisperTranscriptionProgress,
  type CaptionAnimationStyle,
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
import type {
  OmniVoiceProviderModel,
  OmniVoiceTranslationProvider,
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
  handleGenerateSubtitles: () => Promise<void>;
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
                  onClick={handleGenerateSubtitles}
                  disabled={isTranscribing}
                  className="w-full py-2 bg-primary hover:bg-primary/80 text-black rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-2"
                >
                  <Captions size={14} />
                  Generate with OmniVoice
                </button>
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
