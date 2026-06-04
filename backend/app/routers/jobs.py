from fastapi import APIRouter, HTTPException

from backend.app.schemas.jobs import JobCreateRequest
from backend.infrastructure.stores.history import list_history
from backend.infrastructure.stores.jobs import JOB_STATUSES, get_job_store

router = APIRouter()

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

