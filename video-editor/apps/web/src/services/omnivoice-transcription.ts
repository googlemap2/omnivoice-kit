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

interface OmniVoiceWord {
  word?: string;
  text?: string;
  start: number | null;
  end: number | null;
}

interface OmniVoiceSegment {
  id?: number | string;
  start: number;
  end: number;
  text: string;
  words?: OmniVoiceWord[];
}

interface OmniVoiceTranscriptionResponse {
  text?: string;
  language?: string | null;
  duration?: number | null;
  segments?: OmniVoiceSegment[];
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

  const words = (segment.words || [])
    .filter((word) => word.start !== null && word.end !== null)
    .map((word) => {
      const wordStart = Number(word.start);
      const wordEnd = Number(word.end);
      return {
        text: String(word.word || word.text || "").trim(),
        startTime: clip.startTime + (wordStart - inPoint),
        endTime: clip.startTime + (wordEnd - inPoint),
      };
    })
    .filter(
      (word) =>
        word.text &&
        Number.isFinite(word.startTime) &&
        Number.isFinite(word.endTime) &&
        word.endTime > startTime &&
        word.startTime < endTime,
    );

  return {
    id: `omnivoice-sub-${segment.id ?? Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`,
    text: String(segment.text || "").trim(),
    startTime,
    endTime,
    words: words.length > 0 ? words : undefined,
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
  formData.append("response_format", "verbose_json");
  formData.append("word_timestamps", "true");

  appendOptional(formData, "language", options.language);
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

  const payload = (await response.json()) as OmniVoiceTranscriptionResponse;
  const segments = payload.segments || [];
  const subtitles = segments
    .map((segment) =>
      toSubtitle(segment, clip, options.animationStyle || "word-highlight"),
    )
    .filter((subtitle): subtitle is Subtitle => Boolean(subtitle));

  return subtitles;
}
