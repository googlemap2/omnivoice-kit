import React from "react";
import { Loader2, Zap } from "lucide-react";
import { AutoReframeSection } from "../";
import { InspectorSection } from "../shell/InspectorSection";
import { AutoEditPanel } from "../../panels/AutoEditPanel";
import { HighlightExtractorPanel } from "../../panels/HighlightExtractorPanel";

export interface AiTabProps {
  clipId: string;
  clipType: string | null;
  showVideoControls: boolean;
  showAudioEffects: boolean;
  showVideoEffects: boolean;
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
  handleRemoveBackground,
  handleEnhanceAudio,
  handleAutoColor,
  isEnhancingAudio,
  audioEnhanced,
  isApplyingSelectedClipEffect,
}) => {
  const hasBuiltInTools =
    clipType === "video" ||
    showAudioEffects ||
    showVideoControls ||
    showVideoEffects;

  if (!hasBuiltInTools) {
    return (
      <div className="rounded-xl border border-border bg-background-secondary/60 p-4">
        <div className="flex items-start gap-2">
          <Zap size={15} className="mt-0.5 text-text-secondary" />
          <div>
            <div className="text-xs font-bold text-text-primary">
              Built-in Editor AI Tools
            </div>
            <p className="mt-1 text-[10px] leading-4 text-text-muted">
              No built-in AI tools are available for this clip type.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4 rounded-xl border border-border bg-background-secondary/60 p-3">
        <div className="flex items-start gap-2">
          <Zap size={15} className="mt-0.5 text-text-secondary" />
          <div>
            <div className="text-xs font-bold text-text-primary">
              Built-in Editor AI Tools
            </div>
            <p className="mt-1 text-[10px] leading-4 text-text-muted">
              Local/editor-native tools. OmniVoice backend features are in the
              OmnivoiceAI tab.
            </p>
          </div>
        </div>
      </div>

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
