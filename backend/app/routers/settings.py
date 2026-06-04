import requests
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.app.routers.common import _settings_without_provider_models
from backend.app.schemas.settings import (
    ProviderModelChatRequest,
    ProviderModelRequest,
    SettingsRequest,
    TranslationProviderSettingsRequest,
)
from backend.infrastructure.stores.provider_models import cloud_provider_to_settings_config, get_provider_model_store
from backend.domain.settings import (
    AppSettings,
    load_settings,
    merge_translation_provider_config,
    save_settings,
)
from backend.services.translation_service import provider_model_chat_completion

router = APIRouter()

@router.get("/v1/settings")
def get_settings() -> dict:
    return {
        "object": "settings",
        "data": _settings_without_provider_models(load_settings()).to_dict(),
    }


@router.put("/v1/settings")
def update_settings(request: SettingsRequest) -> dict:
    current = load_settings()
    provider_config = current.translation_provider_config
    if request.translation_provider_config is not None:
        provider_config = request.translation_provider_config
    settings = AppSettings(
        default_model=request.default_model,
        default_device=request.default_device or None,
        default_effect_preset=request.default_effect_preset,
        output_dir=request.output_dir,
        default_translation_provider=(
            request.default_translation_provider or current.default_translation_provider
        ),
        translation_provider_config=provider_config,
        huggingface_token=request.huggingface_token if request.huggingface_token is not None else current.huggingface_token,
    )
    saved = save_settings(settings)
    return {
        "object": "settings",
        "data": _settings_without_provider_models(saved).to_dict(),
    }


def _load_cloud_models_from_config(cloud: dict[str, Any]) -> list[dict[str, Any]]:
    base_url = str(cloud.get("base_url") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=400, detail="Cloud provider base_url is required.")

    headers = {"Accept": "application/json"}
    api_key = str(cloud.get("api_key") or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Cloud provider request failed: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail="Cloud provider returned non-JSON response.") from e

    raw_models = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(raw_models, list):
        raise HTTPException(status_code=502, detail="Cloud provider response does not contain a model list.")

    models: list[dict[str, Any]] = []
    for item in raw_models:
        if isinstance(item, dict):
            model_id = item.get("id")
            if isinstance(model_id, str) and model_id.strip():
                models.append(item)
        elif isinstance(item, str) and item.strip():
            models.append({"id": item.strip()})
    return models


@router.get("/v1/provider-models")
def list_provider_models() -> dict:
    try:
        records = get_provider_model_store().list_provider_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": [record.to_dict() for record in records],
    }


@router.post("/v1/provider-models")
def create_provider_model(request: ProviderModelRequest) -> dict:
    try:
        record = get_provider_model_store().save_cloud_provider(
            {
                "provider_name": request.provider_name,
                "base_url": request.base_url,
                "api_key": request.api_key or "",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {"object": "provider_model", "data": record.to_dict()}


@router.patch("/v1/provider-models/{provider_id}")
def update_provider_model(provider_id: str, request: ProviderModelRequest) -> dict:
    try:
        if get_provider_model_store().get_provider_model(provider_id) is None:
            raise HTTPException(status_code=404, detail="Provider model not found.")
        record = get_provider_model_store().save_cloud_provider(
            {
                "provider_name": request.provider_name,
                "base_url": request.base_url,
                "api_key": request.api_key or "",
            },
            provider_id=provider_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {"object": "provider_model", "data": record.to_dict()}


@router.delete("/v1/provider-models/{provider_id}")
def delete_provider_model(provider_id: str) -> dict:
    try:
        deleted = get_provider_model_store().delete_provider_model(provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider model not found.")
    return {"object": "provider_model", "deleted": True}


@router.post("/v1/provider-models/{provider_id}/models")
def load_provider_model_models(provider_id: str) -> dict:
    try:
        record = get_provider_model_store().get_provider_model(provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    if record is None:
        raise HTTPException(status_code=404, detail="Provider model not found.")

    cloud = cloud_provider_to_settings_config(record)
    models = _load_cloud_models_from_config(cloud)
    cloud["available_models"] = [model["id"] for model in models]
    try:
        get_provider_model_store().save_cloud_provider(cloud, provider_id=provider_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": models,
    }


@router.post("/v1/provider-models/chat")
def chat_provider_model(request: ProviderModelChatRequest) -> dict:
    try:
        content = provider_model_chat_completion(
            request.provider_model_id,
            request.message,
            model_name=request.model,
            system_prompt=request.system,
            temperature=request.temperature,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Provider model request failed: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "provider_model_chat",
        "data": {
            "provider_model_id": request.provider_model_id,
            "model": request.model,
            "content": content,
        },
    }


@router.patch("/v1/settings/translation-providers")
def update_translation_provider_settings(request: TranslationProviderSettingsRequest) -> dict:
    current = load_settings()
    provider_config = merge_translation_provider_config(
        current.translation_provider_config,
        google_api_key=request.google_api_key,
        google_disabled=request.google_disabled,
        deepl_api_key=request.deepl_api_key,
        microsoft_api_key=request.microsoft_api_key,
        microsoft_region=request.microsoft_region,
        mymemory_api_key=request.mymemory_api_key,
        nllb_model_id=request.nllb_model_id,
    )
    saved = save_settings(
        AppSettings(
            default_model=current.default_model,
            default_device=current.default_device,
            default_effect_preset=current.default_effect_preset,
            output_dir=current.output_dir,
            default_translation_provider=current.default_translation_provider,
            translation_provider_config=provider_config,
            huggingface_token=current.huggingface_token,
        )
    )
    return {"object": "settings", "data": _settings_without_provider_models(saved).to_dict()}
