"use client";

import { SettingsPanel } from "../../../features/settings/SettingsPanel";
import { useStudio } from "../../../features/studio/StudioContext";

export default function SettingsPage() {
  const studio = useStudio();

  return (
    <SettingsPanel
      settings={studio.settings}
      setSettings={studio.setSettings}
      statuses={studio.statuses}
      meta={studio.meta}
      onSave={studio.saveSettings}
    />
  );
}
