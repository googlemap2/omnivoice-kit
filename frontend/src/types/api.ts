export type Option = {
  id: string;
  label: string;
};

export type Voice = {
  id: string;
  name: string;
  type: string;
  language: string | null;
  prompt_path: string;
  ref_text: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ModelStatus = {
  repo_id: string;
  local_path: string;
  installed: boolean;
  has_config: boolean;
  has_weights: boolean;
};

export type AppSettings = {
  default_model: string;
  default_device: string | null;
  default_effect_preset: "raw" | "normalize" | "broadcast";
  output_dir: string;
  default_translation_provider: string;
  translation_provider_config: Record<string, unknown>;
  huggingface_token?: string | null;
};

export type Meta = {
  omnivoice_models: Option[];
  asr_models: Option[];
  languages: Option[];
  translation_languages: Option[];
  instructs: string[];
  effect_presets: string[];
  transcription_formats: string[];
  subtitle_formats: string[];
  devices: string[];
  compute_types: string[];
};

export type TranslationProvider = {
  id: string;
  name: string;
  provider_type: string;
  available: boolean;
  message?: string | null;
};

export type HistoryEntry = {
  id: string;
  created_at: string;
  mode: string;
  model: string | null;
  text: string;
  voice: string | null;
  language: string | null;
  output_path: string | null;
  status: string;
};

export type SubtitleSegment = {
  id: number;
  start: number;
  end: number;
  text: string;
  speaker?: string | null;
  metadata?: Record<string, unknown>;
};

export type DubbingResult = {
  id: string;
  folder_name: string;
  input_path: string;
  extracted_audio_path: string;
  dubbed_audio_path: string;
  dubbed_video_path: string | null;
  srt_path: string;
  vtt_path: string;
  segment_count: number;
  source_language: string | null;
  target_language: string | null;
  voice: string;
  speakers: string[];
};

export type JobRecord = {
  id: string;
  created_at: string;
  updated_at: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "canceled";
  params: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  progress: number;
};

export const emptyMeta: Meta = {
  omnivoice_models: [],
  asr_models: [],
  languages: [],
  translation_languages: [],
  instructs: [],
  effect_presets: ["raw", "normalize", "broadcast"],
  transcription_formats: ["json", "text", "verbose_json", "srt", "vtt"],
  subtitle_formats: ["srt", "vtt"],
  devices: ["", "cpu", "cuda", "mps"],
  compute_types: ["", "int8", "float16", "float32"],
};
