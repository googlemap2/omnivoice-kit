"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import LibraryMusicIcon from "@mui/icons-material/LibraryMusic";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Box, Button, Chip, IconButton, Paper, Stack, TextField, Tooltip, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { useStudio } from "../../../components/studio/StudioContext";

export default function VoicesPage() {
  const studio = useStudio();
  const [search, setSearch] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const filteredVoices = useMemo(() => {
    const query = search.trim().toLowerCase();
    return studio.voices.filter((voice) => {
      const matchesFavorite = !favoriteOnly || voice.favorite;
      const haystack = [
        voice.id,
        voice.name,
        voice.language || "",
        voice.type,
        voice.ref_text || "",
        voice.notes || "",
        ...(voice.tags || []),
      ]
        .join(" ")
        .toLowerCase();
      return matchesFavorite && (!query || haystack.includes(query));
    });
  }, [favoriteOnly, search, studio.voices]);

  return (
    <WorkspaceShell
      icon={<LibraryMusicIcon />}
      title="Voice Profiles"
      action={
        <Button startIcon={<AutoAwesomeIcon />} variant="contained" onClick={studio.createVoice}>
          Create Voice
        </Button>
      }
    >
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "360px 1fr" }, gap: 2 }}>
        <Stack spacing={2}>
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            Import voice package
            <input
              hidden
              type="file"
              accept=".zip,.voicepkg.zip,application/zip"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void studio.importVoicePackage(file);
                event.currentTarget.value = "";
              }}
            />
          </Button>
          <TextField
            label="Speaker ID"
            value={studio.newVoiceId}
            onChange={(event) => studio.setNewVoiceId(event.target.value)}
          />
          <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
            {studio.newVoiceFile ? studio.newVoiceFile.name : "Choose reference audio"}
            <input
              hidden
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => studio.setNewVoiceFile(event.target.files?.[0] || null)}
            />
          </Button>
          <SelectField label="Language" value={studio.language} onChange={studio.setLanguage} options={studio.meta.languages} />
          <TextField
            label="Reference transcript"
            multiline
            minRows={6}
            value={studio.newVoiceText}
            onChange={(event) => studio.setNewVoiceText(event.target.value)}
          />
        </Stack>
        <Stack spacing={1}>
          <Paper variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
              <TextField
                size="small"
                placeholder="Search voices"
                slotProps={{ htmlInput: { "aria-label": "Search voices" } }}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                sx={{ flex: 1 }}
              />
              <Button
                variant={favoriteOnly ? "contained" : "outlined"}
                startIcon={favoriteOnly ? <StarIcon /> : <StarBorderIcon />}
                onClick={() => setFavoriteOnly((current) => !current)}
              >
                Favorites
              </Button>
            </Stack>
          </Paper>
          {filteredVoices.map((voice) => (
            <VoiceProfileCard key={voice.id} voice={voice} studio={studio} />
          ))}
          {filteredVoices.length === 0 && (
            <Typography sx={{ color: "text.secondary", fontSize: 13 }}>No voice profiles match this view.</Typography>
          )}
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}

function VoiceProfileCard({ voice, studio }: { voice: ReturnType<typeof useStudio>["voices"][number]; studio: ReturnType<typeof useStudio> }) {
  const tags = voice.tags || [];

  return (
    <Paper variant="outlined" sx={{ p: 1.25, bgcolor: "#252526" }}>
      <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={2}>
        <Box sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
            <Typography sx={{ fontWeight: 600 }}>{voice.name || voice.id}</Typography>
            <Chip size="small" label={voice.language || "auto"} />
            {voice.favorite && <Chip size="small" color="warning" variant="outlined" label="Favorite" />}
          </Stack>
          <Typography sx={{ mt: 0.5, fontSize: 12, color: "text.secondary", overflowWrap: "anywhere" }}>
            {voice.prompt_path}
          </Typography>
          {voice.notes && (
            <Typography sx={{ mt: 0.5, fontSize: 12, color: "text.secondary" }}>{voice.notes}</Typography>
          )}
          {tags.length > 0 && (
            <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap" sx={{ mt: 1 }}>
              {tags.map((tag) => (
                <Chip key={tag} size="small" variant="outlined" label={tag} />
              ))}
            </Stack>
          )}
        </Box>
        <Stack direction="row" spacing={0.5} alignSelf={{ xs: "flex-start", sm: "center" }}>
          <Tooltip title="Generate preview">
            <IconButton size="small" onClick={() => void studio.generateVoicePreview(voice.id)}>
              <PlayArrowIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Export voice package">
            <IconButton size="small" onClick={() => void studio.exportVoiceProfile(voice.id)}>
              <DownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={voice.favorite ? "Remove favorite" : "Mark favorite"}>
            <IconButton size="small" onClick={() => void studio.updateVoiceProfile(voice.id, { favorite: !voice.favorite })}>
              {voice.favorite ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete voice profile">
            <IconButton
              size="small"
              color="error"
              onClick={() => {
                if (window.confirm(`Delete voice profile "${voice.id}"?`)) {
                  void studio.deleteVoiceProfile(voice.id);
                }
              }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>
    </Paper>
  );
}
