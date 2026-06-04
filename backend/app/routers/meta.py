from fastapi import APIRouter

from backend.services.transcription_service import ASR_MODEL_CHOICES, TRANSCRIPTION_FORMATS
from backend.domain.audio import EFFECT_PRESETS
from backend.services.speech_service import OMNIVOICE_LANGUAGE_CHOICES, OMNIVOICE_MODEL_CHOICES, VALID_INSTRUCTS
from backend.services.diarization_service import DEFAULT_DIARIZATION_MODEL_ID
from backend.domain.settings import DEFAULT_NLLB_MODEL_ID
from backend.services.subtitle_service import SUBTITLE_FORMATS
from backend.services.translation_service import TRANSLATION_LANGUAGE_CHOICES


router = APIRouter()


@router.get("/v1/meta")
def get_meta() -> dict:
    return {
        "omnivoice_models": [
            {"label": label, "id": model_id} for label, model_id in OMNIVOICE_MODEL_CHOICES
        ],
        "asr_models": [{"label": label, "id": model_id} for label, model_id in ASR_MODEL_CHOICES],
        "languages": [{"label": label, "id": language_id} for label, language_id in OMNIVOICE_LANGUAGE_CHOICES],
        "translation_languages": [
            {"label": label, "id": language_id} for label, language_id in TRANSLATION_LANGUAGE_CHOICES
        ],
        "instructs": list(VALID_INSTRUCTS),
        "effect_presets": list(EFFECT_PRESETS),
        "transcription_formats": list(TRANSCRIPTION_FORMATS),
        "subtitle_formats": list(SUBTITLE_FORMATS),
        "devices": ["", "cpu", "cuda", "mps"],
        "compute_types": ["", "int8", "float16", "float32"],
        "default_nllb_model_id": DEFAULT_NLLB_MODEL_ID,
        "default_diarization_model_id": DEFAULT_DIARIZATION_MODEL_ID,
    }


@router.get("/v1/languages")
def list_languages() -> dict:
    return {
        "object": "list",
        "data": [{"label": label, "id": language_id} for label, language_id in OMNIVOICE_LANGUAGE_CHOICES],
    }

