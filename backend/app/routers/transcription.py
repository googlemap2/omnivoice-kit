from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.paths import DATA_DIR
from backend.app.routers.common import _format_translated_payload, _translated_transcription_payload
from backend.infrastructure.stores.jobs import get_job_store
from backend.services.transcription_service import (
    DEFAULT_ASR_MODEL_ID,
    TRANSCRIPTION_FORMATS,
    format_transcription,
    transcribe_file,
)

router = APIRouter()

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

    upload_dir = DATA_DIR / "uploads"
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
