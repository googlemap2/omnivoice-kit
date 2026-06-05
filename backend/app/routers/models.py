from fastapi import APIRouter, Body, HTTPException

from backend.app.schemas.models import ModelInstallRequest, ModelUnloadRequest
from backend.services.speech_service import OMNIVOICE_MODEL_CHOICES, unload_cached_models
from backend.infrastructure.model_store import install_model, list_model_statuses
from backend.domain.settings import load_settings


router = APIRouter()


@router.get("/v1/models")
def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "owned_by": "local",
                "display_name": label,
            }
            for label, model_id in OMNIVOICE_MODEL_CHOICES
        ],
    }


@router.get("/v1/model-status")
def list_model_status() -> dict:
    return {
        "object": "list",
        "data": [status.to_dict() for status in list_model_statuses()],
    }


@router.post("/v1/model-status/install")
def install_model_endpoint(request: ModelInstallRequest) -> dict:
    try:
        token = request.hf_token or load_settings().huggingface_token
        status = install_model(request.repo_id, token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "model_status",
        "data": status.to_dict(),
        "message": "Model is installed." if status.installed else "Model install finished but files are incomplete.",
    }


@router.post("/v1/models/unload")
def unload_models_endpoint(
    request: ModelUnloadRequest | None = Body(default=None),
) -> dict:
    data = unload_cached_models(
        model_arg=request.repo_id if request else None,
        feature=request.feature if request else None,
    )
    return {
        "object": "model_unload",
        "data": data,
        "message": "Model cache unloaded.",
    }
