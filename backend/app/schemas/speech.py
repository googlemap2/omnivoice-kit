from typing import Literal

from pydantic import BaseModel, Field

from backend.infrastructure.model_store import DEFAULT_MODEL_ID


class SpeechRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL_ID)
    input: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    response_format: Literal["wav"] = "wav"
    language: str | None = None
    instruct_items: list[str] = Field(default_factory=list)
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0
    duration: float | None = None
    denoise: bool = True
    preprocess_prompt: bool = True
    postprocess_output: bool = True
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    queued: bool = False


class VoiceDesignRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL_ID)
    input: str = Field(min_length=1)
    language: str | None = None
    instruct_items: list[str] = Field(min_length=1)
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0
    duration: float | None = None
    denoise: bool = True
    postprocess_output: bool = True
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    queued: bool = False


class EmotionSpeechRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL_ID)
    input: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    response_format: Literal["wav"] = "wav"
    language: str | None = None
    default_instruct: str | None = None
    tag_aliases: dict[str, str] = Field(default_factory=dict)
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0
    duration: float | None = None
    denoise: bool = True
    preprocess_prompt: bool = True
    postprocess_output: bool = True
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    gap_ms: int = 120
    queued: bool = False

