from typing import Literal

from pydantic import BaseModel, Field

from backend.infrastructure.model_store import DEFAULT_MODEL_ID


class SettingsRequest(BaseModel):
    default_model: str = DEFAULT_MODEL_ID
    default_device: Literal["", "cpu", "cuda", "mps"] | None = None
    default_effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    output_dir: str = "outputs"
    default_translation_provider: str | None = None
    translation_provider_config: dict | None = None
    huggingface_token: str | None = None


class TranslationProviderSettingsRequest(BaseModel):
    google_api_key: str | None = None
    google_disabled: bool | None = None
    deepl_api_key: str | None = None
    microsoft_api_key: str | None = None
    microsoft_region: str | None = None
    mymemory_api_key: str | None = None
    nllb_model_id: str | None = None


class ProviderModelRequest(BaseModel):
    provider_name: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    api_key: str | None = None

