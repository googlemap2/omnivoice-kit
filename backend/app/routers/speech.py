import json
import tempfile
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

from backend.app.errors import generation_error as _generation_error
from backend.app.errors import server_error as _server_error
from backend.app.routers.common import _voice_debug_headers, _wav_response
from backend.app.schemas.speech import EmotionSpeechRequest, SpeechRequest, VoiceDesignRequest
from backend.infrastructure.model_store import DEFAULT_MODEL_ID
from backend.infrastructure.stores.jobs import get_job_store
from backend.services.emotion_tts_service import load_tag_aliases, render_emotion_tts_speaker_id
from backend.services.speech_service import (
    generate_clone_with_ref_audio,
    generate_clone_with_speaker_id,
    generate_voice_design,
    get_profile_store,
)
from backend.domain.settings import load_settings
from backend.paths import DATA_DIR, SPEAKERS_PATH

router = APIRouter()

@router.post("/v1/audio/speech")
def create_speech(request: SpeechRequest) -> Response:
    if request.queued:
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "speaker",
                "text": request.input,
                "speaker_id": request.voice,
                "model_id": request.model,
                "language": request.language,
                "instruct_items": request.instruct_items,
                "num_step": request.num_step,
                "guidance_scale": request.guidance_scale,
                "speed": request.speed,
                "duration": request.duration,
                "denoise": request.denoise,
                "preprocess_prompt": request.preprocess_prompt,
                "postprocess_output": request.postprocess_output,
                "effect_preset": request.effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
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
        raise _generation_error(status)
    profile = get_profile_store().get_profile(request.voice)
    return _wav_response(
        audio,
        headers=_voice_debug_headers(profile, model=request.model) if profile else None,
    )


@router.post("/v1/audio/speech/clone")
async def create_speech_from_reference(
    text: str = Form(...),
    ref_audio: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL_ID),
    ref_text: str | None = Form(None),
    language: str | None = Form(None),
    instruct_items: str = Form("[]"),
    num_step: int = Form(16),
    guidance_scale: float = Form(2.0),
    speed: float = Form(1.0),
    duration: float | None = Form(None),
    denoise: bool = Form(True),
    preprocess_prompt: bool = Form(True),
    postprocess_output: bool = Form(True),
    effect_preset: Literal["raw", "normalize", "broadcast"] = Form("raw"),
    queued: bool = Form(False),
) -> Response:
    try:
        parsed_instruct = json.loads(instruct_items) if instruct_items else []
        if not isinstance(parsed_instruct, list):
            parsed_instruct = []
    except json.JSONDecodeError:
        parsed_instruct = []

    suffix = Path(ref_audio.filename or "ref.wav").suffix or ".wav"
    if queued:
        upload_dir = DATA_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / f"speech_ref_{uuid4().hex}{suffix}"
        upload_path.write_bytes(await ref_audio.read())
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "clone",
                "text": text,
                "ref_audio": str(upload_path),
                "ref_text": ref_text,
                "model_id": model,
                "language": language,
                "instruct_items": parsed_instruct,
                "num_step": num_step,
                "guidance_scale": guidance_scale,
                "speed": speed,
                "duration": duration,
                "denoise": denoise,
                "preprocess_prompt": preprocess_prompt,
                "postprocess_output": postprocess_output,
                "effect_preset": effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await ref_audio.read())
        tmp_path = tmp.name
    try:
        audio, status = generate_clone_with_ref_audio(
            text=text,
            ref_audio=tmp_path,
            ref_text=ref_text,
            model_id=model,
            language=language,
            instruct_items=parsed_instruct,
            num_step=num_step,
            guidance_scale=guidance_scale,
            speed=speed,
            duration=duration,
            denoise=denoise,
            preprocess_prompt=preprocess_prompt,
            postprocess_output=postprocess_output,
            effect_preset=effect_preset,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if audio is None:
        raise _generation_error(status)
    return _wav_response(audio)


@router.post("/v1/audio/speech/design")
def create_speech_voice_design(request: VoiceDesignRequest) -> Response:
    if request.queued:
        job = get_job_store().create_job(
            "speech",
            {
                "mode": "design",
                "text": request.input,
                "model_id": request.model,
                "language": request.language,
                "instruct_items": request.instruct_items,
                "num_step": request.num_step,
                "guidance_scale": request.guidance_scale,
                "speed": request.speed,
                "duration": request.duration,
                "denoise": request.denoise,
                "postprocess_output": request.postprocess_output,
                "effect_preset": request.effect_preset,
            },
        )
        return JSONResponse({"object": "job", "data": job.to_dict()})
    audio, status = generate_voice_design(
        text=request.input,
        model_id=request.model,
        language=request.language,
        instruct_items=request.instruct_items,
        num_step=request.num_step,
        guidance_scale=request.guidance_scale,
        speed=request.speed,
        duration=request.duration,
        denoise=request.denoise,
        postprocess_output=request.postprocess_output,
        effect_preset=request.effect_preset,
    )
    if audio is None:
        raise _generation_error(status)
    return _wav_response(audio)


@router.post("/v1/audio/speech/emotion-script")
def create_emotion_script_speech(request: EmotionSpeechRequest) -> Response:
    try:
        tag_aliases = load_tag_aliases(None)
        tag_aliases.update({key.strip().lower(): value.strip() for key, value in request.tag_aliases.items()})
        if request.queued:
            job = get_job_store().create_job(
                "speech",
                {
                    "mode": "emotion",
                    "script_text": request.input,
                    "speaker_id": request.voice,
                    "speakers_path": str(SPEAKERS_PATH),
                    "model_id": request.model,
                    "language": request.language,
                    "default_instruct": request.default_instruct,
                    "tag_aliases": tag_aliases,
                    "num_step": request.num_step,
                    "guidance_scale": request.guidance_scale,
                    "speed": request.speed,
                    "duration": request.duration,
                    "denoise": request.denoise,
                    "preprocess_prompt": request.preprocess_prompt,
                    "postprocess_output": request.postprocess_output,
                    "effect_preset": request.effect_preset,
                    "device": load_settings().default_device,
                    "gap_ms": request.gap_ms,
                },
            )
            return JSONResponse({"object": "job", "data": job.to_dict()})
        result = render_emotion_tts_speaker_id(
            script_text=request.input,
            speaker_id=request.voice,
            speakers_path=str(SPEAKERS_PATH),
            model_id=request.model,
            language=request.language,
            default_instruct=request.default_instruct,
            tag_aliases=tag_aliases,
            num_step=request.num_step,
            guidance_scale=request.guidance_scale,
            speed=request.speed,
            duration=request.duration,
            denoise=request.denoise,
            preprocess_prompt=request.preprocess_prompt,
            postprocess_output=request.postprocess_output,
            effect_preset=request.effect_preset,
            device=load_settings().default_device,
            gap_ms=request.gap_ms,
        )
    except Exception as e:
        raise _server_error(e) from e
    profile = get_profile_store(SPEAKERS_PATH).get_profile(request.voice)
    return _wav_response(
        (result["sample_rate"], result["audio"]),
        headers=_voice_debug_headers(profile, model=request.model) if profile else None,
    )
