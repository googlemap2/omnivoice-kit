"use client";

import { useStudio } from "../../../features/studio/StudioContext";
import { TranslatePanel } from "../../../features/translation/TranslatePanel";

export default function TranslationPage() {
  const studio = useStudio();

  return (
    <TranslatePanel
      meta={studio.meta}
      providers={studio.providers}
      provider={studio.provider}
      setProvider={studio.setProvider}
      sourceLanguage={studio.sourceLanguage}
      setSourceLanguage={studio.setSourceLanguage}
      targetLanguage={studio.targetLanguage}
      setTargetLanguage={studio.setTargetLanguage}
      translateText={studio.translateText}
      setTranslateText={studio.setTranslateText}
      translatedText={studio.translatedText}
      onTranslate={studio.translate}
    />
  );
}
