import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import TranslateIcon from "@mui/icons-material/Translate";
import { Box, Button, Stack, TextField } from "@mui/material";
import { WorkspaceShell } from "../../components/layout/WorkspaceShell";
import { SelectField } from "../../components/ui/SelectField";
import type { Meta, TranslationProvider } from "../../types/api";

type TranslatePanelProps = {
  meta: Meta;
  providers: TranslationProvider[];
  provider: string;
  setProvider: (provider: string) => void;
  sourceLanguage: string;
  setSourceLanguage: (language: string) => void;
  targetLanguage: string;
  setTargetLanguage: (language: string) => void;
  translateText: string;
  setTranslateText: (text: string) => void;
  translatedText: string;
  onTranslate: () => void;
};

export function TranslatePanel(props: TranslatePanelProps) {
  return (
    <WorkspaceShell
      icon={<TranslateIcon />}
      title="Translation"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={props.onTranslate}>
          Translate
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1}>
            <SelectField
              label="Provider"
              value={props.provider}
              onChange={props.setProvider}
              options={props.providers.map((item) => ({ id: item.id, label: item.name }))}
            />
            <SelectField
              label="From"
              value={props.sourceLanguage}
              onChange={props.setSourceLanguage}
              options={props.meta.translation_languages}
            />
            <SelectField
              label="To"
              value={props.targetLanguage}
              onChange={props.setTargetLanguage}
              options={props.meta.translation_languages}
            />
          </Stack>
          <TextField
            label="Source text"
            multiline
            minRows={18}
            value={props.translateText}
            onChange={(event) => props.setTranslateText(event.target.value)}
          />
        </Stack>
        <TextField
          label="Translated text"
          multiline
          minRows={21}
          value={props.translatedText}
          InputProps={{ readOnly: true }}
        />
      </Box>
    </WorkspaceShell>
  );
}
