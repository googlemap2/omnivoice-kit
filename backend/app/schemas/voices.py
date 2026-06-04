from typing import Literal

from pydantic import BaseModel, Field


class VoiceRenameRequest(BaseModel):
    new_id: str = Field(min_length=1)


class VoiceProfileUpdateRequest(BaseModel):
    name: str | None = None
    language: str | None = None
    tags: list[str] | None = None
    favorite: bool | None = None
    notes: str | None = None
    preview_path: str | None = None


class VoicePreviewRequest(BaseModel):
    text: str | None = None
    language: str | None = None
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0

