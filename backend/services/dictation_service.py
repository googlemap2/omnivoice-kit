from dataclasses import asdict, dataclass
from pathlib import Path

from backend.paths import DATA_DIR
from typing import Any
from uuid import uuid4


DEFAULT_DICTATION_MODEL_ID = "Systran/faster-whisper-large-v3"
DICTATION_UPLOAD_DIR = DATA_DIR / "dictation"
DICTATION_VAD_PARAMETERS = {
    "min_silence_duration_ms": 500,
    "speech_pad_ms": 200,
}


@dataclass(frozen=True)
class DictationEvent:
    type: str
    text: str = ""
    segments: list[dict[str, Any]] | None = None
    bytes_received: int | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


def media_suffix_from_mime(mime_type: str | None) -> str:
    mime = (mime_type or "").split(";")[0].strip().lower()
    if mime in {"audio/webm", "video/webm"}:
        return ".webm"
    if mime in {"audio/ogg", "application/ogg"}:
        return ".ogg"
    if mime in {"audio/mpeg", "audio/mp3"}:
        return ".mp3"
    if mime in {"audio/mp4", "audio/x-m4a"}:
        return ".m4a"
    return ".wav"


def partial_event(bytes_received: int) -> dict[str, Any]:
    return DictationEvent(type="partial", text="", bytes_received=bytes_received).to_dict()


def result_event(result: Any) -> dict[str, Any]:
    return DictationEvent(
        type="final",
        text=result.text,
        segments=[segment.to_dict() for segment in result.segments],
    ).to_dict()


def fake_result_event(audio_bytes: bytes) -> dict[str, Any]:
    return DictationEvent(
        type="final",
        text=f"fake dictation transcript ({len(audio_bytes)} bytes)",
        segments=[],
        bytes_received=len(audio_bytes),
    ).to_dict()


def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    mime_type: str | None = None,
    model_id: str = DEFAULT_DICTATION_MODEL_ID,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    word_timestamps: bool = False,
    beam_size: int = 5,
) -> Any:
    if not audio_bytes:
        raise ValueError("No audio bytes received.")

    from backend.services.transcription_service import transcribe_file

    DICTATION_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = DICTATION_UPLOAD_DIR / f"dictation_{uuid4().hex}{media_suffix_from_mime(mime_type)}"
    try:
        path.write_bytes(audio_bytes)
        return transcribe_file(
            audio_path=path,
            model_id=model_id,
            language=language,
            device=device,
            compute_type=compute_type,
            word_timestamps=word_timestamps,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters=DICTATION_VAD_PARAMETERS,
            condition_on_previous_text=False,
            no_speech_threshold=0.8,
            hallucination_silence_threshold=1.0,
        )
    finally:
        path.unlink(missing_ok=True)
