from fastapi import APIRouter

from backend.services.diagnostics_service import (
    clear_logs,
    diagnostics_snapshot,
    memory_snapshot,
    read_logs,
)


router = APIRouter()


@router.get("/v1/diagnostics")
def get_diagnostics() -> dict:
    return {"object": "diagnostics", "data": diagnostics_snapshot()}


@router.get("/v1/diagnostics/memory")
def get_memory_diagnostics() -> dict:
    return {"object": "memory_diagnostics", "data": memory_snapshot()}


@router.get("/v1/logs")
def get_logs(limit: int = 300) -> dict:
    return {"object": "logs", "data": read_logs(limit=limit)}


@router.delete("/v1/logs")
def delete_logs() -> dict:
    clear_logs()
    return {"object": "logs", "message": "Logs cleared."}
