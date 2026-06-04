from fastapi import APIRouter

from backend.app.schemas.translation import TranslateRequest
from backend.services.translation_service import list_providers, translate_segments, translate_text

router = APIRouter()

@router.get("/v1/translation/providers")
def list_translation_providers() -> dict:
    return {
        "object": "list",
        "data": [provider.to_dict() for provider in list_providers()],
    }


@router.post("/v1/translation/translate")
def translate(request: TranslateRequest) -> dict:
    try:
        if request.segments:
            segment_payload = [segment.model_dump() for segment in request.segments]
            if request.provider_model_id:
                result = translate_segments_with_provider_model(
                    segments=segment_payload,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_model_id=request.provider_model_id,
                    provider_model_name=request.provider_model_name,
                )
            else:
                result = translate_segments(
                    segments=segment_payload,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_id=request.provider,
                )
        else:
            if not request.text or not request.text.strip():
                raise HTTPException(status_code=400, detail="text or segments is required.")
            if request.provider_model_id:
                result = translate_text_with_provider_model(
                    text=request.text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_model_id=request.provider_model_id,
                    provider_model_name=request.provider_model_name,
                )
            else:
                result = translate_text(
                    text=request.text,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    provider_id=request.provider,
                )
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"{type(e).__name__}: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "translation",
        "data": result.to_dict(),
    }

