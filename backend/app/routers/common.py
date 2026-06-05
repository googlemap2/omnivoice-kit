import hashlib
from io import BytesIO
from typing import Any

import soundfile as sf
from fastapi import HTTPException
from fastapi.responses import Response

from backend.domain.settings import AppSettings
from backend.paths import resolve_path
from backend.services.subtitle_service import export_subtitle
from backend.services.translation_service import (
    translate_segments,
    translate_segments_with_provider_model,
)

def _settings_without_provider_models(settings: AppSettings) -> AppSettings:
    return AppSettings(
        default_model=settings.default_model,
        default_device=settings.default_device,
        default_effect_preset=settings.default_effect_preset,
        output_dir=settings.output_dir,
        default_translation_provider=settings.default_translation_provider,
        translation_provider_config=settings.translation_provider_config,
        huggingface_token=settings.huggingface_token,
    )


def _wav_response(
    audio: tuple[int, Any] | None,
    detail: str = "Generation failed.",
    headers: dict[str, str] | None = None,
) -> Response:
    if audio is None:
        raise HTTPException(status_code=400, detail=detail)
    sampling_rate, samples = audio
    buffer = BytesIO()
    sf.write(buffer, samples, sampling_rate, format="WAV", subtype="PCM_16")
    return Response(
        content=buffer.getvalue(),
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'attachment; filename="speech.wav"',
            **(headers or {}),
        },
    )


def _voice_prompt_debug(profile: Any) -> dict[str, Any]:
    prompt_path = resolve_path(profile.prompt_path) if profile.prompt_path else None
    prompt_sha256 = None
    if prompt_path and prompt_path.exists() and prompt_path.is_file():
        digest = hashlib.sha256()
        with prompt_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        prompt_sha256 = digest.hexdigest()

    return {
        "prompt_resolved_path": str(prompt_path) if prompt_path else None,
        "prompt_exists": bool(prompt_path and prompt_path.exists()),
        "prompt_sha256": prompt_sha256,
    }


def _voice_debug_headers(profile: Any, *, model: str | None = None) -> dict[str, str]:
    prompt_debug = _voice_prompt_debug(profile)
    headers = {
        "X-OmniVoice-Voice": str(profile.id),
        "X-OmniVoice-Prompt-Exists": "true" if prompt_debug["prompt_exists"] else "false",
    }
    if model:
        headers["X-OmniVoice-Model"] = model
    if prompt_debug["prompt_sha256"]:
        headers["X-OmniVoice-Prompt-Sha256"] = str(prompt_debug["prompt_sha256"])
    return headers


def _translated_transcription_payload(
    result,
    *,
    source_language: str | None,
    target_language: str | None,
    translation_provider: str | None,
    provider_model_id: str | None,
    provider_model_name: str | None,
) -> dict[str, Any]:
    if not target_language:
        raise ValueError("target_language is required when translate is enabled.")

    raw_segments = [segment.to_dict() for segment in result.segments]
    if provider_model_id:
        translated = translate_segments_with_provider_model(
            segments=raw_segments,
            source_language=source_language or result.language,
            target_language=target_language,
            provider_model_id=provider_model_id,
            provider_model_name=provider_model_name,
        )
    else:
        translated = translate_segments(
            segments=raw_segments,
            source_language=source_language or result.language,
            target_language=target_language,
            provider_id=translation_provider,
        )
    translated_segments = translated.segments or []
    output_segments = []
    for index, raw in enumerate(raw_segments):
        translated_segment = translated_segments[index] if index < len(translated_segments) else None
        translated_text = (translated_segment.translated_text if translated_segment else None) or raw["text"]
        output_segments.append({**raw, "text": translated_text, "metadata": {"source_text": raw["text"]}})

    return {
        "text": translated.text,
        "language": result.language,
        "duration": result.duration,
        "translation": {
            "source_language": source_language or result.language,
            "target_language": target_language,
            "provider": translated.provider,
        },
        "segments": output_segments,
        "raw_segments": raw_segments,
        "raw_srt": export_subtitle(raw_segments, "srt"),
        "raw_vtt": export_subtitle(raw_segments, "vtt"),
        "translated_srt": export_subtitle(output_segments, "srt"),
        "translated_vtt": export_subtitle(output_segments, "vtt"),
    }


def _format_translated_payload(payload: dict[str, Any], response_format: str, include_subtitle_artifacts: bool):
    if include_subtitle_artifacts:
        return {**payload, "response_format": response_format}
    if response_format == "text":
        return payload["text"]
    if response_format == "json":
        return {"text": payload["text"]}
    if response_format == "verbose_json":
        return {
            key: payload[key]
            for key in ("text", "language", "duration", "translation", "segments")
            if key in payload
        }
    if response_format == "srt":
        return payload["translated_srt"]
    if response_format == "vtt":
        return payload["translated_vtt"]
    raise ValueError(f"Unsupported transcription format: {response_format}")


def _voice_profile_dict(profile: Any) -> dict[str, Any]:
    return {
        "id": profile.id,
        "object": "voice",
        "name": profile.name,
        "type": profile.type,
        "language": profile.language,
        "prompt_path": profile.prompt_path,
        **_voice_prompt_debug(profile),
        "ref_text": profile.ref_text,
        "tags": profile.tags or [],
        "favorite": profile.favorite,
        "notes": profile.notes,
        "preview_path": profile.preview_path,
        "asset_dir": profile.asset_dir,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }

