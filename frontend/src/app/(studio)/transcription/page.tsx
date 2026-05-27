"use client";

import { useStudio } from "../../../features/studio/StudioContext";
import { TranscribePanel } from "../../../features/transcription/TranscribePanel";

export default function TranscriptionPage() {
  const studio = useStudio();

  return (
    <TranscribePanel
      meta={studio.meta}
      language={studio.language}
      setLanguage={studio.setLanguage}
      transcribeFile={studio.transcribeFile}
      setTranscribeFile={studio.setTranscribeFile}
      transcribeFormat={studio.transcribeFormat}
      setTranscribeFormat={studio.setTranscribeFormat}
      transcription={studio.transcription}
      onTranscribe={studio.transcribe}
    />
  );
}
