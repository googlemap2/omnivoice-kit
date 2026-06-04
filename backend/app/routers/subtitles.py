from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, Response

from backend.app.schemas.subtitles import SubtitleExportRequest
from backend.services.subtitle_service import export_subtitle, parse_subtitle
from backend.services.subtitle_service import SUBTITLE_FORMATS

router = APIRouter()

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

