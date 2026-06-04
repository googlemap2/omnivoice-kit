from typing import Any, Literal

from pydantic import BaseModel, Field


class SubtitleSegmentRequest(BaseModel):
    id: int = 0
    start: float
    end: float
    text: str = Field(min_length=1)
    speaker: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SubtitleExportRequest(BaseModel):
    format: Literal["srt", "vtt"] = "srt"
    segments: list[SubtitleSegmentRequest] = Field(default_factory=list)

