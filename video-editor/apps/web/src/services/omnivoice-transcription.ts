import type {
  CaptionAnimationStyle,
  Clip,
  MediaItem,
  Subtitle,
} from "@openreel/core";
import type { WhisperTranscriptionProgress } from "@openreel/core";
import { useSettingsStore } from "../stores/settings-store";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_ASR_MODEL = "Systran/faster-whisper-large-v3";

interface OmniVoiceSegment {
  id?: number | string;
  start: number;
  end: number;
  text: string;
}

interface GenerateCaptionOptions {
  language?: string;
  targetLanguage?: string;
  animationStyle?: CaptionAnimationStyle;
}

const getApiBaseUrl = (): string => {
  const configured = useSettingsStore.getState().omnivoiceApiBaseUrl;
  return (configured || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
};

const getMediaFile = async (mediaItem: MediaItem): Promise<File> => {
  if (mediaItem.blob) {
    if (mediaItem.blob instanceof File) {
      return mediaItem.blob;
    }
    return new File([mediaItem.blob], mediaItem.name || "media", {
      type: mediaItem.blob.type || "application/octet-stream",
    });
  }

  if (mediaItem.fileHandle) {
    return mediaItem.fileHandle.getFile();
  }

  throw new Error("No media source available for transcription.");
};

const appendOptional = (
  formData: FormData,
  key: string,
  value: string | number | boolean | undefined,
) => {
  if (value === undefined || value === "") return;
  formData.append(key, String(value));
};

const parseSrtTimestamp = (value: string): number | null => {
  const match = value.trim().match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/);
  if (!match) return null;

  const [, hours, minutes, seconds, milliseconds] = match;
  return (
    Number(hours) * 3600 +
    Number(minutes) * 60 +
    Number(seconds) +
    Number(milliseconds) / 1000
  );
};

const parseSrt = (srt: string): OmniVoiceSegment[] => {
  return srt
    .replace(/\r\n/g, "\n")
    .split(/\n{2,}/)
    .map((block): OmniVoiceSegment | null => {
      const lines = block
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      const timingIndex = lines.findIndex((line) => line.includes("-->"));
      if (timingIndex === -1) return null;

      const [startRaw, endRaw] = lines[timingIndex]
        .split("-->")
        .map((part) => part.trim().split(/\s+/)[0]);
      const start = parseSrtTimestamp(startRaw || "");
      const end = parseSrtTimestamp(endRaw || "");
      if (start === null || end === null || end <= start) return null;

      return {
        id: lines[0],
        start,
        end,
        text: lines.slice(timingIndex + 1).join("\n").trim(),
      };
    })
    .filter((segment): segment is OmniVoiceSegment => Boolean(segment?.text));
};

const toSubtitle = (
  segment: OmniVoiceSegment,
  clip: Clip,
  animationStyle: CaptionAnimationStyle,
): Subtitle | null => {
  const inPoint = clip.inPoint || 0;
  const outPoint = clip.outPoint || inPoint + clip.duration;
  const segmentStart = Number(segment.start);
  const segmentEnd = Number(segment.end);

  if (!Number.isFinite(segmentStart) || !Number.isFinite(segmentEnd)) {
    return null;
  }

  const clippedStart = Math.max(segmentStart, inPoint);
  const clippedEnd = Math.min(segmentEnd, outPoint);
  if (clippedEnd <= clippedStart) return null;

  const startTime = clip.startTime + (clippedStart - inPoint);
  const endTime = clip.startTime + (clippedEnd - inPoint);

  return {
    id: `omnivoice-sub-${segment.id ?? Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`,
    text: String(segment.text || "").trim(),
    startTime,
    endTime,
    animationStyle,
    style: {
      fontFamily: "Inter",
      fontSize: 24,
      color: "#ffffff",
      backgroundColor: "rgba(0, 0, 0, 0.7)",
      position: "bottom",
      highlightColor: "#ffff00",
    },
  };
};

export async function generateOmniVoiceCaptions(
  clip: Clip,
  mediaItem: MediaItem,
  options: GenerateCaptionOptions,
  onProgress?: (progress: WhisperTranscriptionProgress) => void,
): Promise<Subtitle[]> {
  onProgress?.({
    phase: "extracting",
    progress: 0,
    message: "Preparing media for OmniVoice...",
  });

  const file = await getMediaFile(mediaItem);
  const formData = new FormData();
  formData.append("file", file, file.name || mediaItem.name || "media");
  formData.append("model", DEFAULT_ASR_MODEL);
  formData.append("response_format", "srt");

  appendOptional(formData, "language", options.language);
  appendOptional(formData, "source_language", options.language);
  appendOptional(formData, "translate", Boolean(options.targetLanguage));
  appendOptional(formData, "target_language", options.targetLanguage);

  onProgress?.({
    phase: "transcribing",
    progress: 30,
    message: "Transcribing with OmniVoice backend...",
  });

  const response = await fetch(`${getApiBaseUrl()}/v1/audio/transcriptions`, {
    method: "POST",
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OmniVoice transcription failed: ${response.status} ${errorText}`);
  }

  onProgress?.({
    phase: "processing",
    progress: 85,
    message: "Building captions...",
  });

  const srt = await response.text();
  const segments = parseSrt(srt);
  const subtitles = segments
    .map((segment) =>
      toSubtitle(segment, clip, options.animationStyle || "word-highlight"),
    )
    .filter((subtitle): subtitle is Subtitle => Boolean(subtitle));

  return subtitles;
}
