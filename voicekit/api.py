from io import BytesIO
from typing import Literal

import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from voicekit.core import (
    OMNIVOICE_LANGUAGE_CHOICES,
    OMNIVOICE_MODEL_CHOICES,
    generate_clone_with_speaker_id,
    get_profile_store,
)
from voicekit.model_store import DEFAULT_MODEL_ID, install_model, list_model_statuses


app = FastAPI(title="OmniVoice Kit API", version="0.1.0")


class SpeechRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL_ID)
    input: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    response_format: Literal["wav"] = "wav"
    language: str | None = None
    instruct_items: list[str] = Field(default_factory=list)
    num_step: int = 16
    guidance_scale: float = 2.0
    speed: float = 1.0
    duration: float | None = None
    denoise: bool = True
    preprocess_prompt: bool = True
    postprocess_output: bool = True


class ModelInstallRequest(BaseModel):
    repo_id: str = DEFAULT_MODEL_ID


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
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


@app.get("/v1/model-status")
def list_model_status() -> dict:
    return {
        "object": "list",
        "data": [status.to_dict() for status in list_model_statuses()],
    }


@app.post("/v1/model-status/install")
def install_model_endpoint(request: ModelInstallRequest) -> dict:
    try:
        status = install_model(request.repo_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "model_status",
        "data": status.to_dict(),
        "message": "Model is installed." if status.installed else "Model install finished but files are incomplete.",
    }


@app.get("/v1/voices")
def list_voices() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": profile.id,
                "object": "voice",
                "name": profile.name,
                "type": profile.type,
                "language": profile.language,
            }
            for profile in get_profile_store().list_profiles()
        ],
    }


@app.get("/v1/languages")
def list_languages() -> dict:
    return {
        "object": "list",
        "data": [{"label": label, "id": language_id} for label, language_id in OMNIVOICE_LANGUAGE_CHOICES],
    }


@app.post("/v1/audio/speech")
def create_speech(request: SpeechRequest) -> Response:
    audio, status = generate_clone_with_speaker_id(
        text=request.input,
        speaker_id=request.voice,
        model_id=request.model,
        language=request.language,
        instruct_items=request.instruct_items,
        num_step=request.num_step,
        guidance_scale=request.guidance_scale,
        speed=request.speed,
        duration=request.duration,
        denoise=request.denoise,
        preprocess_prompt=request.preprocess_prompt,
        postprocess_output=request.postprocess_output,
    )
    if audio is None:
        raise HTTPException(status_code=400, detail=status)

    sampling_rate, samples = audio
    buffer = BytesIO()
    sf.write(buffer, samples, sampling_rate, format="WAV", subtype="PCM_16")
    return Response(
        content=buffer.getvalue(),
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="speech.wav"'},
    )
