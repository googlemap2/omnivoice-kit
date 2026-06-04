from pydantic import BaseModel, Field


class TranslationSegmentRequest(BaseModel):
    id: int = 0
    start: float | None = None
    end: float | None = None
    text: str = Field(min_length=1)


class TranslateRequest(BaseModel):
    text: str | None = None
    segments: list[TranslationSegmentRequest] = Field(default_factory=list)
    source_language: str | None = None
    target_language: str | None = None
    provider: str | None = None
    provider_model_id: str | None = None
    provider_model_name: str | None = None

