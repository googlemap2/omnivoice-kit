import json
import requests
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import soundfile as sf
from fastapi import File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from starlette.concurrency import run_in_threadpool

from voicekit.app.dependencies import parse_speaker_voice_map
from voicekit.app.errors import generation_error as _generation_error
from voicekit.app.errors import server_error as _server_error
from voicekit.app.errors import websocket_error as _websocket_error
from fastapi import APIRouter

router = APIRouter()
from voicekit.app.schemas.dubbing import DiarizationMergeRequest, DubbingRequest
from voicekit.app.schemas.jobs import JobCreateRequest
from voicekit.app.schemas.settings import (
    ProviderModelRequest,
    SettingsRequest,
    TranslationProviderSettingsRequest,
)
from voicekit.app.schemas.speech import EmotionSpeechRequest, SpeechRequest, VoiceDesignRequest
from voicekit.app.schemas.subtitles import SubtitleExportRequest
from voicekit.app.schemas.translation import TranslateRequest
from voicekit.app.schemas.voices import VoicePreviewRequest, VoiceProfileUpdateRequest, VoiceRenameRequest
from voicekit.services.transcription_service import (
    DEFAULT_ASR_MODEL_ID,
    TRANSCRIPTION_FORMATS,
    format_transcription,
    transcribe_file,
)
from voicekit.services.speech_service import (
    create_speaker_id,
    delete_speaker_id,
    generate_clone_with_ref_audio,
    generate_clone_with_speaker_id,
    generate_voice_design,
    get_profile_store,
    rename_speaker_id,
)
from voicekit.services.emotion_tts_service import load_tag_aliases, render_emotion_tts_speaker_id
from voicekit.services.diarization_service import (
    DEFAULT_DIARIZATION_MODEL_ID,
    assign_speakers_to_segments,
    diarization_availability,
    diarize_file,
)
from voicekit.dictation import fake_result_event, partial_event, result_event, transcribe_audio_bytes
from voicekit.services.dubbing_service import dub_file
from voicekit.infrastructure.stores.history import list_history
from voicekit.infrastructure.stores.jobs import JOB_STATUSES, get_job_store
from voicekit.infrastructure.model_store import DEFAULT_MODEL_ID
from voicekit.infrastructure.stores.provider_models import cloud_provider_to_settings_config, get_provider_model_store
from voicekit.settings import (
    AppSettings,
    load_settings,
    merge_translation_provider_config,
    save_settings,
)
from voicekit.services.subtitle_service import export_subtitle, parse_subtitle
from voicekit.subtitles import SUBTITLE_FORMATS
from voicekit.services.translation_service import (
    list_providers,
    translate_segments,
    translate_segments_with_provider_model,
    translate_text,
    translate_text_with_provider_model,
)

def _settings_without_provider_models(settings: AppSettings) -> AppSettings:
    return AppSettings(
        default_model=settings.default_model,
        default_device=settings.default_device,
        default_effect_preset=settings.default_effect_preset,
        output_dir=settings.output_dir,
        default_translation_provider=settings.default_translation_provider,
        translation_provider_config=settings.translation_provider_config,
        huggingface_token=settings.huggingface_token,
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


def _translated_transcription_payload(
    result,
    *,
    source_language: str | None,
    target_language: str | None,
    translation_provider: str | None,
    provider_model_id: str | None,
    provider_model_name: str | None,
) -> dict[str, Any]:
    if not target_language:
        raise ValueError("target_language is required when translate is enabled.")

    raw_segments = [segment.to_dict() for segment in result.segments]
    if provider_model_id:
        translated = translate_segments_with_provider_model(
            segments=raw_segments,
            source_language=source_language or result.language,
            target_language=target_language,
            provider_model_id=provider_model_id,
            provider_model_name=provider_model_name,
        )
    else:
        translated = translate_segments(
            segments=raw_segments,
            source_language=source_language or result.language,
            target_language=target_language,
            provider_id=translation_provider,
        )
    translated_segments = translated.segments or []
    output_segments = []
    for index, raw in enumerate(raw_segments):
        translated_segment = translated_segments[index] if index < len(translated_segments) else None
        translated_text = (translated_segment.translated_text if translated_segment else None) or raw["text"]
        output_segments.append({**raw, "text": translated_text, "metadata": {"source_text": raw["text"]}})

    return {
        "text": translated.text,
        "language": result.language,
        "duration": result.duration,
        "translation": {
            "source_language": source_language or result.language,
            "target_language": target_language,
            "provider": translated.provider,
        },
        "segments": output_segments,
        "raw_segments": raw_segments,
        "raw_srt": export_subtitle(raw_segments, "srt"),
        "raw_vtt": export_subtitle(raw_segments, "vtt"),
        "translated_srt": export_subtitle(output_segments, "srt"),
        "translated_vtt": export_subtitle(output_segments, "vtt"),
    }


def _format_translated_payload(payload: dict[str, Any], response_format: str, include_subtitle_artifacts: bool):
    if include_subtitle_artifacts:
        return {**payload, "response_format": response_format}
    if response_format == "text":
        return payload["text"]
    if response_format == "json":
        return {"text": payload["text"]}
    if response_format == "verbose_json":
        return {
            key: payload[key]
            for key in ("text", "language", "duration", "translation", "segments")
            if key in payload
        }
    if response_format == "srt":
        return payload["translated_srt"]
    if response_format == "vtt":
        return payload["translated_vtt"]
    raise ValueError(f"Unsupported transcription format: {response_format}")


def _voice_profile_dict(profile: Any) -> dict[str, Any]:
    return {
        "id": profile.id,
        "object": "voice",
        "name": profile.name,
        "type": profile.type,
        "language": profile.language,
        "prompt_path": profile.prompt_path,
        "ref_text": profile.ref_text,
        "tags": profile.tags or [],
        "favorite": profile.favorite,
        "notes": profile.notes,
        "preview_path": profile.preview_path,
        "asset_dir": profile.asset_dir,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


@router.get("/v1/settings")
def get_settings() -> dict:
    return {
        "object": "settings",
        "data": _settings_without_provider_models(load_settings()).to_dict(),
    }


@router.put("/v1/settings")
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
        "data": _settings_without_provider_models(saved).to_dict(),
    }


def _load_cloud_models_from_config(cloud: dict[str, Any]) -> list[dict[str, Any]]:
    base_url = str(cloud.get("base_url") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=400, detail="Cloud provider base_url is required.")

    headers = {"Accept": "application/json"}
    api_key = str(cloud.get("api_key") or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Cloud provider request failed: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail="Cloud provider returned non-JSON response.") from e

    raw_models = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(raw_models, list):
        raise HTTPException(status_code=502, detail="Cloud provider response does not contain a model list.")

    models: list[dict[str, Any]] = []
    for item in raw_models:
        if isinstance(item, dict):
            model_id = item.get("id")
            if isinstance(model_id, str) and model_id.strip():
                models.append(item)
        elif isinstance(item, str) and item.strip():
            models.append({"id": item.strip()})
    return models


@router.get("/v1/provider-models")
def list_provider_models() -> dict:
    try:
        records = get_provider_model_store().list_provider_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": [record.to_dict() for record in records],
    }


@router.post("/v1/provider-models")
def create_provider_model(request: ProviderModelRequest) -> dict:
    try:
        record = get_provider_model_store().save_cloud_provider(
            {
                "provider_name": request.provider_name,
                "base_url": request.base_url,
                "api_key": request.api_key or "",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {"object": "provider_model", "data": record.to_dict()}


@router.patch("/v1/provider-models/{provider_id}")
def update_provider_model(provider_id: str, request: ProviderModelRequest) -> dict:
    try:
        if get_provider_model_store().get_provider_model(provider_id) is None:
            raise HTTPException(status_code=404, detail="Provider model not found.")
        record = get_provider_model_store().save_cloud_provider(
            {
                "provider_name": request.provider_name,
                "base_url": request.base_url,
                "api_key": request.api_key or "",
            },
            provider_id=provider_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {"object": "provider_model", "data": record.to_dict()}


@router.delete("/v1/provider-models/{provider_id}")
def delete_provider_model(provider_id: str) -> dict:
    try:
        deleted = get_provider_model_store().delete_provider_model(provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider model not found.")
    return {"object": "provider_model", "deleted": True}


@router.post("/v1/provider-models/{provider_id}/models")
def load_provider_model_models(provider_id: str) -> dict:
    try:
        record = get_provider_model_store().get_provider_model(provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    if record is None:
        raise HTTPException(status_code=404, detail="Provider model not found.")

    cloud = cloud_provider_to_settings_config(record)
    models = _load_cloud_models_from_config(cloud)
    cloud["available_models"] = [model["id"] for model in models]
    try:
        get_provider_model_store().save_cloud_provider(cloud, provider_id=provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": models,
    }


@router.patch("/v1/settings/translation-providers")
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
            huggingface_token=current.huggingface_token,
        )
    )
    return {"object": "settings", "data": _settings_without_provider_models(saved).to_dict()}


@router.get("/v1/voices")
def list_voices() -> dict:
    return {
        "object": "list",
        "data": [_voice_profile_dict(profile) for profile in get_profile_store().list_profiles()],
    }


@router.get("/v1/voice-profiles")
def list_voice_profiles(
    query: str | None = None,
    language: str | None = None,
    favorite: bool | None = None,
    tags: str | None = None,
) -> dict:
    tag_list = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]
    profiles = get_profile_store().search_profiles(query=query, language=language, favorite=favorite, tags=tag_list)
    return {"object": "list", "data": [_voice_profile_dict(profile) for profile in profiles]}


@router.get("/v1/voice-profiles/{voice_id}")
def get_voice_profile(voice_id: str) -> dict:
    profile = get_profile_store().get_profile(voice_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"speaker_id '{voice_id}' not found.")
    return {"object": "voice", "data": _voice_profile_dict(profile)}


@router.get("/v1/voice-profiles/{voice_id}/export")
def export_voice_profile_metadata(voice_id: str) -> JSONResponse:
    profile = get_profile_store().get_profile(voice_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"speaker_id '{voice_id}' not found.")
    payload = {
        "object": "voice_profile_export",
        "format_version": 1,
        "data": _voice_profile_dict(profile),
    }
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="{voice_id}.voice-profile.json"'},
    )


@router.get("/v1/voice-profiles/{voice_id}/package")
def export_voice_profile_package(voice_id: str) -> FileResponse:
    store = get_profile_store()
    try:
        package_dir = Path("data") / "voice_packages"
        package_path = store.export_package(voice_id, package_dir / f"{voice_id}.voicepkg.zip")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise _server_error(e) from e
    return FileResponse(
        package_path,
        media_type="application/zip",
        filename=f"{voice_id}.voicepkg.zip",
    )


@router.post("/v1/voice-profiles/import-package")
async def import_voice_profile_package(
    file: UploadFile = File(...),
    profile_id: str | None = Form(None),
    overwrite: bool = Form(False),
) -> dict:
    suffix = Path(file.filename or "voicepkg.zip").suffix or ".zip"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        profile = get_profile_store().import_package(tmp_path, profile_id=profile_id, overwrite=overwrite)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise _server_error(e) from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return {"object": "voice", "data": _voice_profile_dict(profile)}


@router.post("/v1/voice-profiles")
@router.post("/v1/voices")
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


@router.post("/v1/voice-profiles/{voice_id}/preview")
def generate_voice_profile_preview(voice_id: str, request: VoicePreviewRequest) -> dict:
    store = get_profile_store()
    profile = store.get_profile(voice_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"speaker_id '{voice_id}' not found.")
    text = (request.text or profile.ref_text or f"This is a preview for {profile.name}.").strip()
    audio, status = generate_clone_with_speaker_id(
        text=text,
        speaker_id=voice_id,
        model_id=DEFAULT_MODEL_ID,
        language=request.language or profile.language,
        instruct_items=[],
        num_step=request.num_step,
        guidance_scale=request.guidance_scale,
        speed=request.speed,
        duration=None,
        denoise=True,
        preprocess_prompt=True,
        postprocess_output=True,
        effect_preset=request.effect_preset,
    )
    if audio is None:
        raise _generation_error(status)
    asset_dir = Path(profile.asset_dir or f"assets/voices/{voice_id}")
    asset_dir.mkdir(parents=True, exist_ok=True)
    preview_path = asset_dir / "preview.wav"
    sample_rate, samples = audio
    sf.write(preview_path, samples, sample_rate)
    updated = store.update_profile_metadata(
        profile_id=voice_id,
        preview_path=str(preview_path).replace("\\", "/"),
    )
    return {"object": "voice_preview", "data": _voice_profile_dict(updated), "message": status}


@router.patch("/v1/voice-profiles/{voice_id}")
def update_voice_profile(voice_id: str, request: VoiceProfileUpdateRequest) -> dict:
    try:
        profile = get_profile_store().update_profile_metadata(
            profile_id=voice_id,
            name=request.name,
            language=request.language,
            tags=request.tags,
            favorite=request.favorite,
            notes=request.notes,
            preview_path=request.preview_path,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "voice", "data": _voice_profile_dict(profile)}


@router.delete("/v1/voices/{voice_id}")
def delete_voice(voice_id: str) -> dict:
    message = delete_speaker_id(voice_id)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    if message.startswith("Error") or message.startswith("Please"):
        raise _generation_error(message)
    return {"object": "voice", "message": message}


@router.delete("/v1/voice-profiles/{voice_id}")
def delete_voice_profile(voice_id: str) -> dict:
    return delete_voice(voice_id)


@router.post("/v1/voices/{voice_id}/rename")
def rename_voice(voice_id: str, request: VoiceRenameRequest) -> dict:
    message = rename_speaker_id(voice_id, request.new_id)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    if message.startswith("Error") or message.startswith("Please"):
        raise _generation_error(message)
    return {"object": "voice", "message": message}


@router.get("/v1/translation/providers")
def list_translation_providers() -> dict:
    return {
        "object": "list",
        "data": [provider.to_dict() for provider in list_providers()],
    }


@router.post("/v1/translation/translate")
def translate(request: TranslateRequest) -> dict:
    try:
        if request.segments:
            segment_payload = [segment.model_dump() for segment in request.segments]
            if request.provider_model_id:
                result = translate_segments_with_provider_model(
                    segments=segment_payload,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_model_id=request.provider_model_id,
                    provider_model_name=request.provider_model_name,
                )
            else:
                result = translate_segments(
                    segments=segment_payload,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_id=request.provider,
                )
        else:
            if not request.text or not request.text.strip():
                raise HTTPException(status_code=400, detail="text or segments is required.")
            if request.provider_model_id:
                result = translate_text_with_provider_model(
                    text=request.text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_model_id=request.provider_model_id,
                    provider_model_name=request.provider_model_name,
                )
            else:
                result = translate_text(
                    text=request.text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_id=request.provider,
                )
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"{type(e).__name__}: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "translation",
        "data": result.to_dict(),
    }


@router.get("/v1/generation-history")
def list_generation_history(limit: int = 50) -> dict:
    try:
        data = list_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": data,
    }


@router.get("/v1/jobs")
def list_jobs(limit: int = 50) -> dict:
    try:
        data = [job.to_dict() for job in get_job_store().list_jobs(limit=limit)]
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "list", "data": data, "statuses": list(JOB_STATUSES)}


@router.post("/v1/jobs")
def create_job(request: JobCreateRequest) -> dict:
    try:
        job = get_job_store().create_job(request.type, request.params)
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "job", "data": job.to_dict()}


@router.get("/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = get_job_store().get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"object": "job", "data": job.to_dict()}


@router.post("/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    job = get_job_store().cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"object": "job", "data": job.to_dict()}


@router.delete("/v1/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    deleted = get_job_store().delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"object": "job", "deleted": True, "id": job_id}


@router.post("/v1/subtitles/import")
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


@router.post("/v1/subtitles/export")
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


@router.get("/v1/diarization/status")
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


@router.post("/v1/diarization/diarize")
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


@router.post("/v1/diarization/merge")
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


@router.post("/v1/dubbing/dub")
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
            speaker_voice_map=request.speaker_voice_map,
        )
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "dubbing_job", "data": result.to_dict()}


@router.post("/v1/dubbing/dub-upload")
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
    speaker_voice_map: str | None = Form(None),
    queued: bool = Form(False),
) -> dict:
    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "media").suffix or ".wav"
    upload_path = upload_dir / f"dubbing_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        parsed_speaker_voice_map = parse_speaker_voice_map(speaker_voice_map)
        if queued:
            job = get_job_store().create_job(
                "dubbing",
                {
                    "input_path": str(upload_path),
                    "voice": voice,
                    "target_language": target_language,
                    "folder_name": folder_name or Path(file.filename or "").stem or None,
                    "source_language": source_language,
                    "translation_provider": translation_provider,
                    "tts_model": tts_model,
                    "asr_model": asr_model,
                    "effect_preset": effect_preset,
                    "num_step": num_step,
                    "guidance_scale": guidance_scale,
                    "speed": speed,
                    "enable_diarization": enable_diarization,
                    "diarization_model": diarization_model,
                    "hf_token": hf_token,
                    "speaker_voice_map": parsed_speaker_voice_map,
                },
            )
            return {"object": "job", "data": job.to_dict()}
        result = await run_in_threadpool(
            dub_file,
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
            speaker_voice_map=parsed_speaker_voice_map,
        )
    except Exception as e:
        raise _server_error(e) from e
    return {"object": "dubbing_job", "data": result.to_dict()}


@router.post("/v1/audio/speech")
def create_speech(request: SpeechRequest) -> Response:
    if request.queued:
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "speaker",
                "text": request.input,
                "speaker_id": request.voice,
                "model_id": request.model,
                "language": request.language,
                "instruct_items": request.instruct_items,
                "num_step": request.num_step,
                "guidance_scale": request.guidance_scale,
                "speed": request.speed,
                "duration": request.duration,
                "denoise": request.denoise,
                "preprocess_prompt": request.preprocess_prompt,
                "postprocess_output": request.postprocess_output,
                "effect_preset": request.effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
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


@router.post("/v1/audio/speech/clone")
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
    queued: bool = Form(False),
) -> Response:
    try:
        parsed_instruct = json.loads(instruct_items) if instruct_items else []
        if not isinstance(parsed_instruct, list):
            parsed_instruct = []
    except json.JSONDecodeError:
        parsed_instruct = []

    suffix = Path(ref_audio.filename or "ref.wav").suffix or ".wav"
    if queued:
        upload_dir = Path("data") / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / f"speech_ref_{uuid4().hex}{suffix}"
        upload_path.write_bytes(await ref_audio.read())
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "clone",
                "text": text,
                "ref_audio": str(upload_path),
                "ref_text": ref_text,
                "model_id": model,
                "language": language,
                "instruct_items": parsed_instruct,
                "num_step": num_step,
                "guidance_scale": guidance_scale,
                "speed": speed,
                "duration": duration,
                "denoise": denoise,
                "preprocess_prompt": preprocess_prompt,
                "postprocess_output": postprocess_output,
                "effect_preset": effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
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


@router.post("/v1/audio/speech/design")
def create_speech_voice_design(request: VoiceDesignRequest) -> Response:
    if request.queued:
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "design",
                "text": request.input,
                "model_id": request.model,
                "language": request.language,
                "instruct_items": request.instruct_items,
                "num_step": request.num_step,
                "guidance_scale": request.guidance_scale,
                "speed": request.speed,
                "duration": request.duration,
                "denoise": request.denoise,
                "postprocess_output": request.postprocess_output,
                "effect_preset": request.effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
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


@router.post("/v1/audio/speech/emotion-script")
def create_emotion_script_speech(request: EmotionSpeechRequest) -> Response:
    try:
        tag_aliases = load_tag_aliases(None)
        tag_aliases.update({key.strip().lower(): value.strip() for key, value in request.tag_aliases.items()})
        if request.queued:
            job = get_job_store().create_job(
                "speech",
                {
                    "mode": "emotion",
                    "script_text": request.input,
                    "speaker_id": request.voice,
                    "speakers_path": "speakers.json",
                    "model_id": request.model,
                    "language": request.language,
                    "default_instruct": request.default_instruct,
                    "tag_aliases": tag_aliases,
                    "num_step": request.num_step,
                    "guidance_scale": request.guidance_scale,
                    "speed": request.speed,
                    "duration": request.duration,
                    "denoise": request.denoise,
                    "preprocess_prompt": request.preprocess_prompt,
                    "postprocess_output": request.postprocess_output,
                    "effect_preset": request.effect_preset,
                    "device": load_settings().default_device,
                    "gap_ms": request.gap_ms,
                },
            )
            return JSONResponse({"object": "job", "data": job.to_dict()})
        result = render_emotion_tts_speaker_id(
            script_text=request.input,
            speaker_id=request.voice,
            speakers_path="speakers.json",
            model_id=request.model,
            language=request.language,
            default_instruct=request.default_instruct,
            tag_aliases=tag_aliases,
            num_step=request.num_step,
            guidance_scale=request.guidance_scale,
            speed=request.speed,
            duration=request.duration,
            denoise=request.denoise,
            preprocess_prompt=request.preprocess_prompt,
            postprocess_output=request.postprocess_output,
            effect_preset=request.effect_preset,
            device=load_settings().default_device,
            gap_ms=request.gap_ms,
        )
    except Exception as e:
        raise _server_error(e) from e
    return _wav_response((result["sample_rate"], result["audio"]))


@router.get("/v1/dictation/status")
def get_dictation_status() -> dict:
    return {
        "object": "dictation_status",
        "data": {
            "websocket_path": "/v1/dictation/ws",
            "event_types": ["ready", "partial", "final", "done", "error"],
            "default_model": DEFAULT_ASR_MODEL_ID,
        },
    }


@router.websocket("/v1/dictation/ws")
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


@router.post("/v1/audio/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_ASR_MODEL_ID),
    language: str | None = Form(None),
    response_format: Literal["json", "text", "verbose_json", "srt", "vtt"] = Form("json"),
    device: str | None = Form(None),
    compute_type: str | None = Form(None),
    word_timestamps: bool = Form(False),
    beam_size: int = Form(5),
    translate: bool = Form(False),
    source_language: str | None = Form(None),
    target_language: str | None = Form(None),
    translation_provider: str | None = Form(None),
    provider_model_id: str | None = Form(None),
    provider_model_name: str | None = Form(None),
    include_subtitle_artifacts: bool = Form(False),
    queued: bool = Form(False),
):
    if response_format not in TRANSCRIPTION_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported response_format: {response_format}")

    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio").suffix or ".wav"
    upload_path = upload_dir / f"transcription_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        if queued:
            job = get_job_store().create_job(
                "transcription",
                {
                    "audio_path": str(upload_path),
                    "model_id": model,
                    "language": language,
                    "device": device,
                    "compute_type": compute_type,
                    "word_timestamps": word_timestamps,
                    "beam_size": beam_size,
                    "translate": translate,
                    "source_language": source_language,
                    "target_language": target_language,
                    "translation_provider": translation_provider,
                    "provider_model_id": provider_model_id,
                    "provider_model_name": provider_model_name,
                    "response_format": response_format,
                    "include_subtitle_artifacts": include_subtitle_artifacts,
                },
            )
            return JSONResponse({"object": "job", "data": job.to_dict()})
        result = transcribe_file(
            audio_path=upload_path,
            model_id=model,
            language=language,
            device=device,
            compute_type=compute_type,
            word_timestamps=word_timestamps,
            beam_size=beam_size,
        )
        if translate:
            translated_payload = _translated_transcription_payload(
                result,
                source_language=source_language or result.language,
                target_language=target_language,
                translation_provider=translation_provider,
                provider_model_id=provider_model_id,
                provider_model_name=provider_model_name,
            )
            formatted = _format_translated_payload(translated_payload, response_format, include_subtitle_artifacts)
        else:
            formatted = format_transcription(result, response_format)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"{type(e).__name__}: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    finally:
        if not queued:
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

