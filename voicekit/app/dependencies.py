import json
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse


def output_file_response(path: str) -> FileResponse:
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


def parse_speaker_voice_map(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid speaker_voice_map JSON: {e}") from e
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail="speaker_voice_map must be a JSON object.")
    return {str(key): str(item) for key, item in value.items() if str(key).strip() and str(item).strip()}

