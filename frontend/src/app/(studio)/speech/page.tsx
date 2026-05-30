"use client";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import MicIcon from "@mui/icons-material/Mic";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import SaveAltIcon from "@mui/icons-material/SaveAlt";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Box,
  Button,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Tooltip,
} from "@mui/material";
import { useMemo, useRef, useState, type ChangeEvent, type WheelEvent } from "react";
import { WorkspaceShell } from "../../../components/layout/WorkspaceShell";
import { SelectField } from "../../../components/ui/SelectField";
import { SliderField } from "../../../components/ui/SliderField";
import { useStudio } from "../../../components/studio/StudioContext";
import { downloadBlob } from "../../../lib/api";

const instructLabelsVi: Record<string, string> = {
  "american accent": "Giọng Mỹ",
  "australian accent": "Giọng Úc",
  "british accent": "Giọng Anh",
  "canadian accent": "Giọng Canada",
  child: "Trẻ em",
  "chinese accent": "Giọng Trung Quốc",
  elderly: "Người cao tuổi",
  female: "Nữ",
  "high pitch": "Cao độ cao",
  "indian accent": "Giọng Ấn Độ",
  "japanese accent": "Giọng Nhật",
  "korean accent": "Giọng Hàn",
  "low pitch": "Cao độ thấp",
  male: "Nam",
  "middle-aged": "Trung niên",
  "moderate pitch": "Cao độ vừa",
  "portuguese accent": "Giọng Bồ Đào Nha",
  "russian accent": "Giọng Nga",
  teenager: "Thiếu niên",
  "very high pitch": "Cao độ rất cao",
  "very low pitch": "Cao độ rất thấp",
  whisper: "Thì thầm",
  "young adult": "Thanh niên",
  东北话: "Tiếng Đông Bắc",
  中年: "Trung niên",
  中音调: "Cao độ trung bình",
  云南话: "Tiếng Vân Nam",
  低音调: "Cao độ thấp",
  儿童: "Trẻ em",
  四川话: "Tiếng Tứ Xuyên",
  女: "Nữ",
  宁夏话: "Tiếng Ninh Hạ",
  少年: "Thiếu niên",
  极低音调: "Cao độ rất thấp",
  极高音调: "Cao độ rất cao",
  桂林话: "Tiếng Quế Lâm",
  河南话: "Tiếng Hà Nam",
  济南话: "Tiếng Tế Nam",
  甘肃话: "Tiếng Cam Túc",
  男: "Nam",
  石家庄话: "Tiếng Thạch Gia Trang",
  老年: "Người cao tuổi",
  耳语: "Thì thầm",
  贵州话: "Tiếng Quý Châu",
  陕西话: "Tiếng Thiểm Tây",
  青岛话: "Tiếng Thanh Đảo",
  青年: "Thanh niên",
  高音调: "Cao độ cao",
};

function instructLabel(item: string) {
  return instructLabelsVi[item] || item;
}

const emotionTags = [
  { id: "thoughtful", label: "Suy tư" },
  { id: "chuckles", label: "Cười khúc khích" },
  { id: "whisper", label: "Thì thầm" },
  { id: "surprised", label: "Ngạc nhiên" },
  { id: "excited", label: "Hào hứng" },
  { id: "laughing", label: "Đang cười" },
];

export default function SpeechPage() {
  const studio = useStudio();
  const scriptInputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null);
  const [tagPicker, setTagPicker] = useState<{ open: boolean; query: string; start: number; end: number }>({
    open: false,
    query: "",
    start: 0,
    end: 0,
  });
  const filteredEmotionTags = useMemo(() => {
    const query = tagPicker.query.toLowerCase();
    return emotionTags.filter((tag) => tag.id.includes(query) || tag.label.toLowerCase().includes(query));
  }, [tagPicker.query]);

  function updateTagPicker(text: string, cursor: number | null) {
    if (studio.mode !== "emotion" || cursor === null) {
      setTagPicker((current) => ({ ...current, open: false }));
      return;
    }
    const beforeCursor = text.slice(0, cursor);
    const match = /(^|\s)@([a-z-]*)$/i.exec(beforeCursor);
    if (!match) {
      setTagPicker((current) => ({ ...current, open: false }));
      return;
    }
    const query = match[2] || "";
    setTagPicker({
      open: true,
      query,
      start: cursor - query.length - 1,
      end: cursor,
    });
  }

  function handleScriptChange(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    studio.setSpeechText(event.target.value);
    updateTagPicker(event.target.value, event.target.selectionStart);
  }

  function insertEmotionTag(tag: string) {
    const before = studio.speechText.slice(0, tagPicker.start);
    const after = studio.speechText.slice(tagPicker.end);
    const spacerBefore = before && !/\s$/.test(before) ? " " : "";
    const nextText = `${before}${spacerBefore}[${tag}] ${after}`;
    const nextCursor = before.length + spacerBefore.length + tag.length + 3;
    studio.setSpeechText(nextText);
    setTagPicker((current) => ({ ...current, open: false }));
    window.requestAnimationFrame(() => {
      scriptInputRef.current?.focus();
      scriptInputRef.current?.setSelectionRange(nextCursor, nextCursor);
    });
  }

  return (
    <WorkspaceShell
      icon={<MicIcon />}
      title="Xưởng giọng nói"
      action={
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={studio.generateSpeech}>
          Tạo giọng
        </Button>
      }
    >
      <Tabs value={studio.mode} onChange={(_, value) => studio.setMode(value)}>
        <Tab value="speaker" label="Giọng đã lưu" />
        <Tab value="clone" label="Clone từ audio" />
        <Tab value="design" icon={<AutoAwesomeIcon fontSize="small" />} iconPosition="start" label="Thiết kế giọng" />
        <Tab value="emotion" icon={<AutoAwesomeIcon fontSize="small" />} iconPosition="start" label="Kịch bản cảm xúc" />
      </Tabs>
      <Box sx={{ display: "grid", gridTemplateColumns: "minmax(360px, 1fr) 320px", gap: 2, mt: 2 }}>
        <Stack spacing={2}>
          <Box sx={{ position: "relative" }}>
            <TextField
              label={studio.mode === "emotion" ? "Kịch bản cảm xúc" : "Nội dung nói"}
              multiline
              fullWidth
              minRows={8}
              inputRef={scriptInputRef}
              placeholder={
                studio.mode === "emotion"
                  ? "@thoughtful Chọn xong mấy em soạn kịch bản nhé. @whisper Các vợ kéo xuống cuối. @excited Bấm vào cho anh nha."
                  : undefined
              }
              helperText={
                studio.mode === "emotion"
                  ? "Gõ @ để chọn tag cảm xúc bằng tiếng Việt. UI sẽ chèn thành [tag] trước câu."
                  : undefined
              }
              value={studio.speechText}
              onChange={handleScriptChange}
              onKeyUp={(event) => {
                const target = event.target as HTMLInputElement | HTMLTextAreaElement;
                updateTagPicker(target.value, target.selectionStart);
              }}
              onClick={(event) => {
                const target = event.target as HTMLInputElement | HTMLTextAreaElement;
                updateTagPicker(target.value, target.selectionStart);
              }}
            />
            {tagPicker.open && filteredEmotionTags.length > 0 && (
              <Paper
                variant="outlined"
                sx={{
                  position: "absolute",
                  zIndex: 5,
                  left: 12,
                  right: 12,
                  top: 56,
                  maxWidth: 360,
                  overflow: "hidden",
                  bgcolor: "#252526",
                }}
              >
                <List dense disablePadding>
                  {filteredEmotionTags.map((tag) => (
                    <ListItemButton
                      key={tag.id}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => insertEmotionTag(tag.id)}
                    >
                      <ListItemText primary={tag.label} secondary={`@${tag.id}`} />
                    </ListItemButton>
                  ))}
                </List>
              </Paper>
            )}
          </Box>
          {studio.mode === "clone" && (
            <Stack spacing={1.5}>
              <Button component="label" startIcon={<UploadFileIcon />} variant="outlined">
                {studio.refAudio ? studio.refAudio.name : "Chọn audio tham chiếu"}
                <input
                  hidden
                  type="file"
                  accept="audio/*,video/*"
                  onChange={(event) => studio.setRefAudio(event.target.files?.[0] || null)}
                />
              </Button>
              <TextField
                label="Lời thoại trong audio tham chiếu"
                value={studio.refText}
                onChange={(event) => studio.setRefText(event.target.value)}
              />
            </Stack>
          )}
          {studio.audioUrl && (
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "#252526" }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <audio controls src={studio.audioUrl} style={{ width: "100%" }} />
                <Tooltip title="Tải WAV">
                  <span>
                    <IconButton
                      disabled={!studio.lastAudio}
                      onClick={() => studio.lastAudio && downloadBlob(studio.lastAudio, "speech.wav")}
                    >
                      <SaveAltIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>
            </Paper>
          )}
        </Stack>
        <Stack spacing={2}>
          {(studio.mode === "speaker" || studio.mode === "emotion") && (
            <FormControl size="small">
              <InputLabel>Giọng</InputLabel>
              <Select
                label="Giọng"
                value={studio.selectedVoice}
                onChange={(event) => studio.setSelectedVoice(event.target.value)}
              >
                {studio.voices.map((voice) => (
                  <MenuItem key={voice.id} value={voice.id}>
                    {voice.name || voice.id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <SelectField label="Ngôn ngữ" value={studio.language} onChange={studio.setLanguage} options={studio.meta.languages} />
          <SelectField
            label="Hiệu ứng"
            value={studio.effectPreset}
            onChange={(value) => studio.setEffectPreset(value as "raw" | "normalize" | "broadcast")}
            options={studio.meta.effect_presets.map((id) => ({ id, label: id }))}
          />
          <FormControl size="small">
            <InputLabel>{studio.mode === "emotion" ? "Chỉ dẫn mặc định" : "Chỉ dẫn giọng"}</InputLabel>
            <Select
              multiple
              label={studio.mode === "emotion" ? "Chỉ dẫn mặc định" : "Chỉ dẫn giọng"}
              value={studio.instructs}
              onChange={(event) => studio.setInstructs(event.target.value as string[])}
            >
              {studio.meta.instructs.map((item) => (
                <MenuItem key={item} value={item}>
                  {instructLabel(item)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <SliderField label="Số bước" value={studio.numStep} min={4} max={64} step={1} onChange={studio.setNumStep} />
          <SliderField
            label="Độ bám chỉ dẫn"
            value={studio.guidanceScale}
            min={0.5}
            max={5}
            step={0.1}
            onChange={studio.setGuidanceScale}
          />
          <SliderField label="Tốc độ" value={studio.speed} min={0.5} max={2} step={0.05} onChange={studio.setSpeed} />
          <TextField
            label="Thời lượng (giây)"
            type="number"
            value={studio.duration}
            onChange={(event) => studio.setDuration(event.target.value)}
            slotProps={{
              htmlInput: {
                onWheel: (event: WheelEvent<HTMLInputElement>) => event.currentTarget.blur(),
              },
            }}
          />
          <FormControlLabel
            control={<Switch checked={studio.denoise} onChange={(event) => studio.setDenoise(event.target.checked)} />}
            label="Khử nhiễu"
          />
          {studio.mode !== "design" && (
            <FormControlLabel
              control={
                <Switch
                  checked={studio.preprocessPrompt}
                  onChange={(event) => studio.setPreprocessPrompt(event.target.checked)}
                />
              }
              label="Tiền xử lý giọng mẫu"
            />
          )}
          <FormControlLabel
            control={
              <Switch
                checked={studio.postprocessOutput}
                onChange={(event) => studio.setPostprocessOutput(event.target.checked)}
              />
            }
            label="Hậu xử lý audio"
          />
          {studio.mode !== "emotion" && (
            <FormControlLabel
              control={
                <Switch
                  checked={studio.speechQueued}
                  onChange={(event) => studio.setSpeechQueued(event.target.checked)}
                />
              }
              label="Gửi vào hàng đợi"
            />
          )}
        </Stack>
      </Box>
    </WorkspaceShell>
  );
}
