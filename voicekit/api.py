import json
import logging
import os
import tempfile
import traceback
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
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
from voicekit.diarization import (
    DEFAULT_DIARIZATION_MODEL_ID,
    assign_speakers_to_segments,
    diarization_availability,
    diarize_file,
)
from voicekit.dictation import fake_result_event, partial_event, result_event, transcribe_audio_bytes
from voicekit.dubbing import dub_file
from voicekit.history import list_history
from voicekit.model_store import DEFAULT_MODEL_ID, install_model, list_model_statuses
from voicekit.settings import (
    DEFAULT_NLLB_MODEL_ID,
    AppSettings,
    load_settings,
    merge_translation_provider_config,
    save_settings,
)
from voicekit.subtitles import SUBTITLE_FORMATS, export_subtitle, parse_subtitle
from voicekit.translation import TRANSLATION_LANGUAGE_CHOICES, list_providers, translate_segments, translate_text


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicekit.api")


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


def _server_error(e: Exception) -> HTTPException:
    logger.error("%s: %s\n%s", type(e).__name__, e, traceback.format_exc())
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


async def _websocket_error(websocket: WebSocket, e: Exception) -> None:
    logger.error("%s: %s\n%s", type(e).__name__, e, traceback.format_exc())
    await websocket.send_json({"type": "error", "message": f"{type(e).__name__}: {e}"})


def _output_file_response(path: str) -> FileResponse:
    requested = Path(path)
    if not requested.is_absolute():
        requested = Path.cwd() / requested
    resolved = requested.resolve()
    outputs_root = (Path.cwd() / "outputs").resolve()
    try:
        resolved.relative_to(outputs_root)
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Only files under outputs/ can be served.") from e
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"Output file not found: {path}")
    return FileResponse(resolved)


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
    hf_token: str | None = None


class SettingsRequest(BaseModel):
    default_model: str = DEFAULT_MODEL_ID
    default_device: Literal["", "cpu", "cuda", "mps"] | None = None
    default_effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    output_dir: str = "outputs"
    default_translation_provider: str | None = None
    translation_provider_config: dict | None = None
    huggingface_token: str | None = None


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


class DiarizationMergeRequest(BaseModel):
    subtitles: list[SubtitleSegmentRequest] = Field(default_factory=list)
    diarization: list[dict[str, Any]] = Field(default_factory=list)


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
        "subtitle_formats": list(SUBTITLE_FORMATS),
        "devices": ["", "cpu", "cuda", "mps"],
        "compute_types": ["", "int8", "float16", "float32"],
        "default_nllb_model_id": DEFAULT_NLLB_MODEL_ID,
        "default_diarization_model_id": DEFAULT_DIARIZATION_MODEL_ID,
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
        huggingface_token=request.huggingface_token if request.huggingface_token is not None else current.huggingface_token,
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
        token = request.hf_token or load_settings().huggingface_token
        status = install_model(request.repo_id, token=token)
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


@app.get("/v1/files")
def get_output_file(path: str) -> FileResponse:
    return _output_file_response(path)


@app.post("/v1/subtitles/import")
async def import_subtitle(
    file: UploadFile = File(...),
    format: Literal["srt", "vtt"] | None = Form(None),
    duration: float | None = Form(None),
) -> dict:
    suffix = Path(file.filename or "").suffix.lstrip(".").lower()
    subtitle_format = (format or suffix or "").lower()
    if subtitle_format not in SUBTITLE_FORMATS:
        raise HTTPException(status_code=400, detail="Subtitle format must be srt or vtt.")
    try:
        content = (await file.read()).decode("utf-8-sig")
        segments = parse_subtitle(content, subtitle_format, duration=duration)
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid subtitle encoding: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "subtitle",
        "format": subtitle_format,
        "data": [segment.to_dict() for segment in segments],
    }


@app.post("/v1/subtitles/export")
def export_subtitle_endpoint(request: SubtitleExportRequest) -> Response:
    if not request.segments:
        raise HTTPException(status_code=400, detail="segments must not be empty.")
    try:
        payload = [segment.model_dump() for segment in request.segments]
        content = export_subtitle(payload, request.format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}") from e
    media_type = "application/x-subrip" if request.format == "srt" else "text/vtt"
    return PlainTextResponse(content, media_type=media_type)


@app.get("/v1/diarization/status")
def get_diarization_status() -> dict:
    available, message = diarization_availability()
    return {
        "object": "diarization_status",
        "data": {
            "available": available,
            "message": message,
            "model": DEFAULT_DIARIZATION_MODEL_ID,
        },
    }


@app.post("/v1/diarization/diarize")
async def create_diarization(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_DIARIZATION_MODEL_ID),
    hf_token: str | None = Form(None),
) -> dict:
    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio").suffix or ".wav"
    upload_path = upload_dir / f"diarization_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        segments = diarize_file(upload_path, hf_token=hf_token, model_id=model)
    except Exception as e:
        raise _server_error(e) from e
    finally:
        upload_path.unlink(missing_ok=True)
    return {
        "object": "diarization",
        "data": [segment.to_dict() for segment in segments],
    }


@app.post("/v1/diarization/merge")
def merge_diarization(request: DiarizationMergeRequest) -> dict:
    try:
        subtitles = [segment.model_dump() for segment in request.subtitles]
        assigned = assign_speakers_to_segments(subtitles, request.diarization)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "subtitle",
        "data": [segment.to_dict() for segment in assigned],
    }


@app.post("/v1/dubbing/dub")
def create_dubbing_job(request: DubbingRequest) -> dict:
    try:
        result = dub_file(
            input_path=request.input_path,
            voice=request.voice,
            target_language=request.target_language,
            folder_name=request.folder_name,
            source_language=request.source_language,
            translation_provider=request.translation_provider,
            tts_model=request.tts_model,
            asr_model=request.asr_model,
            effect_preset=request.effect_preset,
            num_step=request.num_step,
            guidance_scale=request.guidance_scale,
            speed=request.speed,
            enable_diarization=request.enable_diarization,
            diarization_model=request.diarization_model,
            hf_token=request.hf_token,
        )
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "dubbing_job", "data": result.to_dict()}


@app.post("/v1/dubbing/dub-upload")
async def create_dubbing_job_from_upload(
    file: UploadFile = File(...),
    voice: str = Form(...),
    target_language: str = Form(...),
    folder_name: str | None = Form(None),
    source_language: str | None = Form(None),
    translation_provider: str | None = Form(None),
    tts_model: str = Form(DEFAULT_MODEL_ID),
    asr_model: str = Form(DEFAULT_ASR_MODEL_ID),
    effect_preset: Literal["raw", "normalize", "broadcast"] = Form("raw"),
    num_step: int = Form(16),
    guidance_scale: float = Form(2.0),
    speed: float = Form(1.0),
    enable_diarization: bool = Form(False),
    diarization_model: str = Form(DEFAULT_DIARIZATION_MODEL_ID),
    hf_token: str | None = Form(None),
) -> dict:
    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "media").suffix or ".wav"
    upload_path = upload_dir / f"dubbing_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        result = dub_file(
            input_path=upload_path,
            voice=voice,
            target_language=target_language,
            folder_name=folder_name or Path(file.filename or "").stem or None,
            source_language=source_language,
            translation_provider=translation_provider,
            tts_model=tts_model,
            asr_model=asr_model,
            effect_preset=effect_preset,
            num_step=num_step,
            guidance_scale=guidance_scale,
            speed=speed,
            enable_diarization=enable_diarization,
            diarization_model=diarization_model,
            hf_token=hf_token,
        )
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "dubbing_job", "data": result.to_dict()}


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


@app.get("/v1/dictation/status")
def get_dictation_status() -> dict:
    return {
        "object": "dictation_status",
        "data": {
            "websocket_path": "/v1/dictation/ws",
            "event_types": ["ready", "partial", "final", "done", "error"],
            "default_model": DEFAULT_ASR_MODEL_ID,
        },
    }


@app.websocket("/v1/dictation/ws")
async def websocket_dictation(
    websocket: WebSocket,
    model: str = DEFAULT_ASR_MODEL_ID,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    word_timestamps: bool = False,
    beam_size: int = 5,
    test_mode: bool = False,
) -> None:
    await websocket.accept()
    audio_chunks: list[bytes] = []
    mime_type: str | None = None
    await websocket.send_json({"type": "ready"})
    try:
        while True:
            message = await websocket.receive()
            if message.get("bytes") is not None:
                chunk = message["bytes"]
                if chunk:
                    audio_chunks.append(chunk)
                    await websocket.send_json(partial_event(sum(len(item) for item in audio_chunks)))
                continue

            text = message.get("text")
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"type": text}

            event_type = payload.get("type")
            if event_type == "start":
                mime_type = payload.get("mime_type") or mime_type
                audio_chunks.clear()
                await websocket.send_json({"type": "ready"})
            elif event_type == "stop":
                audio_bytes = b"".join(audio_chunks)
                if test_mode:
                    await websocket.send_json(fake_result_event(audio_bytes))
                else:
                    result = transcribe_audio_bytes(
                        audio_bytes,
                        mime_type=mime_type,
                        model_id=model,
                        language=language,
                        device=device,
                        compute_type=compute_type,
                        word_timestamps=word_timestamps,
                        beam_size=beam_size,
                    )
                    await websocket.send_json(result_event(result))
                await websocket.send_json({"type": "done"})
                await websocket.close()
                return
            elif event_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        await _websocket_error(websocket, e)
        await websocket.close(code=1011)


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
