import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from backend.paths import DATA_DIR
from backend.app.dependencies import parse_speaker_voice_map
from backend.app.errors import server_error as _server_error
from backend.app.schemas.dubbing import DubbingRequest
from backend.infrastructure.model_store import DEFAULT_MODEL_ID
from backend.infrastructure.stores.jobs import get_job_store
from backend.services.diarization_service import DEFAULT_DIARIZATION_MODEL_ID
from backend.services.dubbing_service import dub_file
from backend.services.transcription_service import DEFAULT_ASR_MODEL_ID

router = APIRouter()

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
    upload_dir = DATA_DIR / "uploads"
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
