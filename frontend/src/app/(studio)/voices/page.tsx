"use client";

import { useStudio } from "../../../features/studio/StudioContext";
import { VoicesPanel } from "../../../features/voices/VoicesPanel";

export default function VoicesPage() {
  const studio = useStudio();

  return (
    <VoicesPanel
      voices={studio.voices}
      language={studio.language}
      setLanguage={studio.setLanguage}
      meta={studio.meta}
      newVoiceId={studio.newVoiceId}
      setNewVoiceId={studio.setNewVoiceId}
      newVoiceText={studio.newVoiceText}
      setNewVoiceText={studio.setNewVoiceText}
      newVoiceFile={studio.newVoiceFile}
      setNewVoiceFile={studio.setNewVoiceFile}
      onCreate={studio.createVoice}
    />
  );
}
