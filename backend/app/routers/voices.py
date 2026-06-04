import tempfile
from pathlib import Path
from typing import Literal

import soundfile as sf
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from backend.app.errors import server_error as _server_error
from backend.infrastructure.model_store import DEFAULT_MODEL_ID
from backend.paths import ASSETS_DIR, DATA_DIR
from backend.app.errors import generation_error as _generation_error
from backend.app.routers.common import _voice_profile_dict
from backend.app.schemas.voices import VoicePreviewRequest, VoiceProfileUpdateRequest, VoiceRenameRequest
from backend.services.speech_service import (
    create_speaker_id,
    delete_speaker_id,
    generate_clone_with_speaker_id,
    get_profile_store,
    rename_speaker_id,
)

router = APIRouter()

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
        package_dir = DATA_DIR / "voice_packages"
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
    asset_dir = Path(profile.asset_dir) if profile.asset_dir else ASSETS_DIR / "voices" / voice_id
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

