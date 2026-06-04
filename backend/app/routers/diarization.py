from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.paths import DATA_DIR
from backend.app.errors import server_error as _server_error
from backend.app.schemas.dubbing import DiarizationMergeRequest
from backend.services.diarization_service import (
    DEFAULT_DIARIZATION_MODEL_ID,
    assign_speakers_to_segments,
    diarization_availability,
    diarize_file,
)

router = APIRouter()

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
    upload_dir = DATA_DIR / "uploads"
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
