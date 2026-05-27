"use client";

import { TtsPanel } from "../../../features/speech/TtsPanel";
import { useStudio } from "../../../features/studio/StudioContext";

export default function SpeechPage() {
  const studio = useStudio();

  return (
    <TtsPanel
      mode={studio.mode}
      setMode={studio.setMode}
      voices={studio.voices}
      meta={studio.meta}
      selectedVoice={studio.selectedVoice}
      setSelectedVoice={studio.setSelectedVoice}
      speechText={studio.speechText}
      setSpeechText={studio.setSpeechText}
      language={studio.language}
      setLanguage={studio.setLanguage}
      effectPreset={studio.effectPreset}
      setEffectPreset={studio.setEffectPreset}
      instructs={studio.instructs}
      setInstructs={studio.setInstructs}
      numStep={studio.numStep}
      setNumStep={studio.setNumStep}
      guidanceScale={studio.guidanceScale}
      setGuidanceScale={studio.setGuidanceScale}
      speed={studio.speed}
      setSpeed={studio.setSpeed}
      duration={studio.duration}
      setDuration={studio.setDuration}
      denoise={studio.denoise}
      setDenoise={studio.setDenoise}
      preprocessPrompt={studio.preprocessPrompt}
      setPreprocessPrompt={studio.setPreprocessPrompt}
      postprocessOutput={studio.postprocessOutput}
      setPostprocessOutput={studio.setPostprocessOutput}
      refText={studio.refText}
      setRefText={studio.setRefText}
      setRefAudio={studio.setRefAudio}
      refAudio={studio.refAudio}
      onGenerate={studio.generateSpeech}
      audioUrl={studio.audioUrl}
      lastAudio={studio.lastAudio}
    />
  );
}
