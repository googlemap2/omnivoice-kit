from fastapi import APIRouter

from voicekit.diagnostics import clear_logs, diagnostics_snapshot, read_logs


router = APIRouter()


@router.get("/v1/diagnostics")
def get_diagnostics() -> dict:
    return {"object": "diagnostics", "data": diagnostics_snapshot()}


@router.get("/v1/logs")
def get_logs(limit: int = 300) -> dict:
    return {"object": "logs", "data": read_logs(limit=limit)}


@router.delete("/v1/logs")
def delete_logs() -> dict:
    clear_logs()
    return {"object": "logs", "message": "Logs cleared."}
