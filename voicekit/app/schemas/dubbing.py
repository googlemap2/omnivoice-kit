from typing import Any, Literal

from pydantic import BaseModel, Field

from voicekit.asr import DEFAULT_ASR_MODEL_ID
from voicekit.diarization import DEFAULT_DIARIZATION_MODEL_ID
from voicekit.model_store import DEFAULT_MODEL_ID
from voicekit.app.schemas.subtitles import SubtitleSegmentRequest


class DubbingRequest(BaseModel):
    input_path: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    target_language: str = Field(min_length=1)
    folder_name: str | None = None
    source_language: str | None = None
    translation_provider: str | None = None
    tts_model: str = DEFAULT_MODEL_ID
    asr_model: str = DEFAULT_ASR_MODEL_ID
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0
    enable_diarization: bool = False
    diarization_model: str = DEFAULT_DIARIZATION_MODEL_ID
    hf_token: str | None = None
    speaker_voice_map: dict[str, str] = Field(default_factory=dict)


class DiarizationMergeRequest(BaseModel):
    subtitles: list[SubtitleSegmentRequest] = Field(default_factory=list)
    diarization: list[dict[str, Any]] = Field(default_factory=list)

