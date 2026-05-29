import json
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from voicekit.audio import EFFECT_PRESETS
from voicekit.asr import (
    ASR_MODEL_CHOICES,
    DEFAULT_ASR_MODEL_ID,
    TRANSCRIPTION_FORMATS,
    format_transcription,
    transcribe_file,
)
from voicekit.core import (
    OMNIVOICE_LANGUAGE_CHOICES,
    OMNIVOICE_MODEL_CHOICES,
    VALID_INSTRUCTS,
    create_speaker_id,
    delete_speaker_id,
    generate_clone_with_ref_audio,
    generate_clone_with_speaker_id,
    generate_voice_design,
    get_profile_store,
    rename_speaker_id,
)
from voicekit.history import list_history
from voicekit.model_store import DEFAULT_MODEL_ID, install_model, list_model_statuses
from voicekit.settings import (
    DEFAULT_NLLB_MODEL_ID,
    AppSettings,
    load_settings,
    merge_translation_provider_config,
    save_settings,
)
from voicekit.translation import TRANSLATION_LANGUAGE_CHOICES, list_providers, translate_segments, translate_text


CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://5365fbfj-3000.asse.devtunnels.ms"
    # Add your frontend/ngrok domains here, for example:
    # "https://your-frontend-domain.ngrok-free.dev",
]


def _cors_origins() -> list[str]:
    raw = os.environ.get("VOICEKIT_CORS_ORIGINS", "")
    env_origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [*CORS_ORIGINS, *env_origins]


app = FastAPI(title="OmniVoice Kit API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _wav_response(audio: tuple[int, Any] | None, detail: str = "Generation failed.") -> Response:
    if audio is None:
        raise HTTPException(status_code=400, detail=detail)
    sampling_rate, samples = audio
    buffer = BytesIO()
    sf.write(buffer, samples, sampling_rate, format="WAV", subtype="PCM_16")
    return Response(
        content=buffer.getvalue(),
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="speech.wav"'},
    )


def _generation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


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


class ModelInstallRequest(BaseModel):
    repo_id: str = DEFAULT_MODEL_ID


class SettingsRequest(BaseModel):
    default_model: str = DEFAULT_MODEL_ID
    default_device: Literal["", "cpu", "cuda", "mps"] | None = None
    default_effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    output_dir: str = "outputs"
    default_translation_provider: str | None = None
    translation_provider_config: dict | None = None


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


class VoiceRenameRequest(BaseModel):
    new_id: str = Field(min_length=1)


class TranslationProviderSettingsRequest(BaseModel):
    google_api_key: str | None = None
    google_disabled: bool | None = None
    deepl_api_key: str | None = None
    microsoft_api_key: str | None = None
    microsoft_region: str | None = None
    mymemory_api_key: str | None = None
    nllb_model_id: str | None = None


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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/meta")
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
        "devices": ["", "cpu", "cuda", "mps"],
        "compute_types": ["", "int8", "float16", "float32"],
        "default_nllb_model_id": DEFAULT_NLLB_MODEL_ID,
    }


@app.get("/v1/models")
def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "owned_by": "local",
                "display_name": label,
            }
            for label, model_id in OMNIVOICE_MODEL_CHOICES
        ],
    }


@app.get("/v1/model-status")
def list_model_status() -> dict:
    return {
        "object": "list",
        "data": [status.to_dict() for status in list_model_statuses()],
    }


@app.get("/v1/settings")
def get_settings() -> dict:
    return {
        "object": "settings",
        "data": load_settings().to_dict(),
    }


@app.put("/v1/settings")
def update_settings(request: SettingsRequest) -> dict:
    current = load_settings()
    provider_config = current.translation_provider_config
    if request.translation_provider_config is not None:
        provider_config = request.translation_provider_config
    settings = AppSettings(
        default_model=request.default_model,
        default_device=request.default_device or None,
        default_effect_preset=request.default_effect_preset,
        output_dir=request.output_dir,
        default_translation_provider=(
            request.default_translation_provider or current.default_translation_provider
        ),
        translation_provider_config=provider_config,
    )
    saved = save_settings(settings)
    return {
        "object": "settings",
        "data": saved.to_dict(),
    }


@app.patch("/v1/settings/translation-providers")
def update_translation_provider_settings(request: TranslationProviderSettingsRequest) -> dict:
    current = load_settings()
    provider_config = merge_translation_provider_config(
        current.translation_provider_config,
        google_api_key=request.google_api_key,
        google_disabled=request.google_disabled,
        deepl_api_key=request.deepl_api_key,
        microsoft_api_key=request.microsoft_api_key,
        microsoft_region=request.microsoft_region,
        mymemory_api_key=request.mymemory_api_key,
        nllb_model_id=request.nllb_model_id,
    )
    saved = save_settings(
        AppSettings(
            default_model=current.default_model,
            default_device=current.default_device,
            default_effect_preset=current.default_effect_preset,
            output_dir=current.output_dir,
            default_translation_provider=current.default_translation_provider,
            translation_provider_config=provider_config,
        )
    )
    return {"object": "settings", "data": saved.to_dict()}


@app.post("/v1/model-status/install")
def install_model_endpoint(request: ModelInstallRequest) -> dict:
    try:
        status = install_model(request.repo_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "model_status",
        "data": status.to_dict(),
        "message": "Model is installed." if status.installed else "Model install finished but files are incomplete.",
    }


@app.get("/v1/voices")
def list_voices() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": profile.id,
                "object": "voice",
                "name": profile.name,
                "type": profile.type,
                "language": profile.language,
                "prompt_path": profile.prompt_path,
                "ref_text": profile.ref_text,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            }
            for profile in get_profile_store().list_profiles()
        ],
    }


@app.post("/v1/voices")
async def create_voice(
    speaker_id: str = Form(...),
    ref_audio: UploadFile = File(...),
    ref_text: str | None = Form(None),
    language: str | None = Form(None),
    save_format: Literal["pt", "npy"] = Form("pt"),
) -> dict:
    suffix = Path(ref_audio.filename or "ref.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await ref_audio.read())
        tmp_path = tmp.name
    try:
        message = create_speaker_id(
            speaker_id=speaker_id,
            ref_audio=tmp_path,
            ref_text=ref_text,
            language=language,
            save_format=save_format,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if message.startswith("Error") or message.startswith("Please"):
        raise _generation_error(message)
    return {"object": "voice", "message": message}


@app.delete("/v1/voices/{voice_id}")
def delete_voice(voice_id: str) -> dict:
    message = delete_speaker_id(voice_id)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    if message.startswith("Error") or message.startswith("Please"):
        raise _generation_error(message)
    return {"object": "voice", "message": message}


@app.post("/v1/voices/{voice_id}/rename")
def rename_voice(voice_id: str, request: VoiceRenameRequest) -> dict:
    message = rename_speaker_id(voice_id, request.new_id)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    if message.startswith("Error") or message.startswith("Please"):
        raise _generation_error(message)
    return {"object": "voice", "message": message}


@app.get("/v1/languages")
def list_languages() -> dict:
    return {
        "object": "list",
        "data": [{"label": label, "id": language_id} for label, language_id in OMNIVOICE_LANGUAGE_CHOICES],
    }


@app.get("/v1/translation/providers")
def list_translation_providers() -> dict:
    return {
        "object": "list",
        "data": [provider.to_dict() for provider in list_providers()],
    }


@app.post("/v1/translation/translate")
def translate(request: TranslateRequest) -> dict:
    try:
        if request.segments:
            segment_payload = [segment.model_dump() for segment in request.segments]
            result = translate_segments(
                segments=segment_payload,
                source_language=request.source_language,
                target_language=request.target_language,
                provider_id=request.provider,
            )
        else:
            if not request.text or not request.text.strip():
                raise HTTPException(status_code=400, detail="text or segments is required.")
            result = translate_text(
                text=request.text,
                source_language=request.source_language,
                target_language=request.target_language,
                provider_id=request.provider,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "translation",
        "data": result.to_dict(),
    }


@app.get("/v1/generation-history")
def list_generation_history(limit: int = 50) -> dict:
    try:
        data = list_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": data,
    }


@app.post("/v1/audio/speech")
def create_speech(request: SpeechRequest) -> Response:
    audio, status = generate_clone_with_speaker_id(
        text=request.input,
        speaker_id=request.voice,
        model_id=request.model,
        language=request.language,
        instruct_items=request.instruct_items,
        num_step=request.num_step,
        guidance_scale=request.guidance_scale,
        speed=request.speed,
        duration=request.duration,
        denoise=request.denoise,
        preprocess_prompt=request.preprocess_prompt,
        postprocess_output=request.postprocess_output,
        effect_preset=request.effect_preset,
    )
    if audio is None:
        raise _generation_error(status)
    return _wav_response(audio)


@app.post("/v1/audio/speech/clone")
async def create_speech_from_reference(
    text: str = Form(...),
    ref_audio: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL_ID),
    ref_text: str | None = Form(None),
    language: str | None = Form(None),
    instruct_items: str = Form("[]"),
    num_step: int = Form(16),
    guidance_scale: float = Form(2.0),
    speed: float = Form(1.0),
    duration: float | None = Form(None),
    denoise: bool = Form(True),
    preprocess_prompt: bool = Form(True),
    postprocess_output: bool = Form(True),
    effect_preset: Literal["raw", "normalize", "broadcast"] = Form("raw"),
) -> Response:
    try:
        parsed_instruct = json.loads(instruct_items) if instruct_items else []
        if not isinstance(parsed_instruct, list):
            parsed_instruct = []
    except json.JSONDecodeError:
        parsed_instruct = []

    suffix = Path(ref_audio.filename or "ref.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await ref_audio.read())
        tmp_path = tmp.name
    try:
        audio, status = generate_clone_with_ref_audio(
            text=text,
            ref_audio=tmp_path,
            ref_text=ref_text,
            model_id=model,
            language=language,
            instruct_items=parsed_instruct,
            num_step=num_step,
            guidance_scale=guidance_scale,
            speed=speed,
            duration=duration,
            denoise=denoise,
            preprocess_prompt=preprocess_prompt,
            postprocess_output=postprocess_output,
            effect_preset=effect_preset,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if audio is None:
        raise _generation_error(status)
    return _wav_response(audio)


@app.post("/v1/audio/speech/design")
def create_speech_voice_design(request: VoiceDesignRequest) -> Response:
    audio, status = generate_voice_design(
        text=request.input,
        model_id=request.model,
        language=request.language,
        instruct_items=request.instruct_items,
        num_step=request.num_step,
        guidance_scale=request.guidance_scale,
        speed=request.speed,
        duration=request.duration,
        denoise=request.denoise,
        postprocess_output=request.postprocess_output,
        effect_preset=request.effect_preset,
    )
    if audio is None:
        raise _generation_error(status)
    return _wav_response(audio)


@app.post("/v1/audio/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_ASR_MODEL_ID),
    language: str | None = Form(None),
    response_format: Literal["json", "text", "verbose_json", "srt", "vtt"] = Form("json"),
    device: str | None = Form(None),
    compute_type: str | None = Form(None),
    word_timestamps: bool = Form(False),
    beam_size: int = Form(5),
):
    if response_format not in TRANSCRIPTION_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported response_format: {response_format}")

    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio").suffix or ".wav"
    upload_path = upload_dir / f"transcription_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        result = transcribe_file(
            audio_path=upload_path,
            model_id=model,
            language=language,
            device=device,
            compute_type=compute_type,
            word_timestamps=word_timestamps,
            beam_size=beam_size,
        )
        formatted = format_transcription(result, response_format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    finally:
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass

    if isinstance(formatted, dict):
        return JSONResponse(formatted)
    media_type = "text/plain"
    if response_format == "srt":
        media_type = "application/x-subrip"
    elif response_format == "vtt":
        media_type = "text/vtt"
    return PlainTextResponse(formatted, media_type=media_type)
