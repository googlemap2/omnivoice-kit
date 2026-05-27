"use client";

import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import TranslateIcon from "@mui/icons-material/Translate";
import { Box, Button, Stack, TextField } from "@mui/material";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";

export default function TranslationPage() {
  const studio = useStudio();

  return (
    <WorkspaceShell
      icon={<TranslateIcon />}
      title="Translation"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={studio.translate}>
          Translate
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1}>
            <SelectField
              label="Provider"
              value={studio.provider}
              onChange={studio.setProvider}
              options={studio.providers.map((item) => ({ id: item.id, label: item.name }))}
            />
            <SelectField
              label="From"
              value={studio.sourceLanguage}
              onChange={studio.setSourceLanguage}
              options={studio.meta.translation_languages}
            />
            <SelectField
              label="To"
              value={studio.targetLanguage}
              onChange={studio.setTargetLanguage}
              options={studio.meta.translation_languages}
            />
          </Stack>
          <TextField
            label="Source text"
            multiline
            minRows={18}
            value={studio.translateText}
            onChange={(event) => studio.setTranslateText(event.target.value)}
          />
        </Stack>
        <TextField
          label="Translated text"
          multiline
          minRows={21}
          value={studio.translatedText}
          InputProps={{ readOnly: true }}
        />
      </Box>
    </WorkspaceShell>
  );
}
