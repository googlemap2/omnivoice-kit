from fastapi import APIRouter

from voicekit.asr import ASR_MODEL_CHOICES, TRANSCRIPTION_FORMATS
from voicekit.audio import EFFECT_PRESETS
from voicekit.core import OMNIVOICE_LANGUAGE_CHOICES, OMNIVOICE_MODEL_CHOICES, VALID_INSTRUCTS
from voicekit.diarization import DEFAULT_DIARIZATION_MODEL_ID
from voicekit.settings import DEFAULT_NLLB_MODEL_ID
from voicekit.subtitles import SUBTITLE_FORMATS
from voicekit.translation import TRANSLATION_LANGUAGE_CHOICES


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

