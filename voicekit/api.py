from io import BytesIO
from pathlib import Path
from typing import Literal
from uuid import uuid4

import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from voicekit.core import (
    OMNIVOICE_LANGUAGE_CHOICES,
    OMNIVOICE_MODEL_CHOICES,
    generate_clone_with_speaker_id,
    get_profile_store,
)
from voicekit.asr import DEFAULT_ASR_MODEL_ID, TRANSCRIPTION_FORMATS, format_transcription, transcribe_file
from voicekit.history import list_history
from voicekit.model_store import DEFAULT_MODEL_ID, install_model, list_model_statuses
from voicekit.settings import AppSettings, load_settings, save_settings


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
    effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"


class ModelInstallRequest(BaseModel):
    repo_id: str = DEFAULT_MODEL_ID


class SettingsRequest(BaseModel):
    default_model: str = DEFAULT_MODEL_ID
    default_device: Literal["", "cpu", "cuda", "mps"] | None = None
    default_effect_preset: Literal["raw", "normalize", "broadcast"] = "raw"
    output_dir: str = "outputs"


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


@app.get("/v1/settings")
def get_settings() -> dict:
    return {
        "object": "settings",
        "data": load_settings().to_dict(),
    }


@app.put("/v1/settings")
def update_settings(request: SettingsRequest) -> dict:
    settings = AppSettings(
        default_model=request.default_model,
        default_device=request.default_device or None,
        default_effect_preset=request.default_effect_preset,
        output_dir=request.output_dir,
    )
    saved = save_settings(settings)
    return {
        "object": "settings",
        "data": saved.to_dict(),
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


@app.get("/v1/generation-history")
def list_generation_history(limit: int = 50) -> dict:
    try:
        data = list_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    return {
        "object": "list",
        "data": data,
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
        effect_preset=request.effect_preset,
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


@app.post("/v1/audio/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_ASR_MODEL_ID),
    language: str | None = Form(None),
    response_format: Literal["json", "text", "verbose_json", "srt", "vtt"] = Form("json"),
    device: str | None = Form(None),
    compute_type: str | None = Form(None),
    word_timestamps: bool = Form(False),
    beam_size: int = Form(5),
):
    if response_format not in TRANSCRIPTION_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported response_format: {response_format}")

    upload_dir = Path("data") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "audio").suffix or ".wav"
    upload_path = upload_dir / f"transcription_input_{uuid4().hex}{suffix}"
    try:
        upload_path.write_bytes(await file.read())
        result = transcribe_file(
            audio_path=upload_path,
            model_id=model,
            language=language,
            device=device,
            compute_type=compute_type,
            word_timestamps=word_timestamps,
            beam_size=beam_size,
        )
        formatted = format_transcription(result, response_format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
    finally:
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass

    if isinstance(formatted, dict):
        return JSONResponse(formatted)
    media_type = "text/plain"
    if response_format == "srt":
        media_type = "application/x-subrip"
    elif response_format == "vtt":
        media_type = "text/vtt"
    return PlainTextResponse(formatted, media_type=media_type)
