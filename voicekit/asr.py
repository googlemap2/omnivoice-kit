from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from voicekit.core import pick_device
from voicekit.model_store import ensure_local_model
from voicekit.subtitles import export_subtitle, from_transcription_result


DEFAULT_ASR_MODEL_ID = "Systran/faster-whisper-large-v3"
ASR_MODEL_CHOICES = [
    ("faster-whisper large-v3", "Systran/faster-whisper-large-v3"),
    ("faster-whisper large-v3 turbo", "Systran/faster-whisper-large-v3-turbo"),
    ("faster-distil-whisper large-v3", "Systran/faster-distil-whisper-large-v3"),
    ("faster-whisper medium", "Systran/faster-whisper-medium"),
    ("faster-whisper small", "Systran/faster-whisper-small"),
    ("faster-whisper base", "Systran/faster-whisper-base"),
]
TRANSCRIPTION_FORMATS = ["json", "text", "verbose_json", "srt", "vtt"]


@dataclass(frozen=True)
class TranscriptionWord:
    word: str
    start: float | None
    end: float | None
    probability: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TranscriptionSegment:
    id: int
    start: float
    end: float
    text: str
    words: list[TranscriptionWord] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.words is None:
            data.pop("words", None)
        return data


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    duration: float | None
    segments: list[TranscriptionSegment]

    def to_dict(self, verbose: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {"text": self.text}
        if verbose:
            data.update(
                {
                    "language": self.language,
                    "duration": self.duration,
                    "segments": [segment.to_dict() for segment in self.segments],
                }
            )
        return data


def _load_faster_whisper_model(model_id: str, device: str | None, compute_type: str | None):
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "Missing dependency 'faster-whisper'. Run `uv sync`, then install ffmpeg for non-WAV inputs."
        ) from e

    selected_device = pick_device(device)
    selected_compute_type = compute_type or ("float16" if selected_device in {"cuda", "mps"} else "int8")
    model_source = model_id
    if "/" in model_id and not Path(model_id).exists():
        model_source = ensure_local_model(model_id)
    return WhisperModel(model_source, device=selected_device, compute_type=selected_compute_type)


def transcribe_file(
    audio_path: str | Path,
    model_id: str = DEFAULT_ASR_MODEL_ID,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    word_timestamps: bool = False,
    beam_size: int = 5,
) -> TranscriptionResult:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    model = _load_faster_whisper_model(model_id, device, compute_type)
    segments_iter, info = model.transcribe(
        str(path),
        language=language or None,
        beam_size=beam_size,
        word_timestamps=word_timestamps,
    )

    segments: list[TranscriptionSegment] = []
    text_parts: list[str] = []
    for index, segment in enumerate(segments_iter):
        segment_text = (segment.text or "").strip()
        text_parts.append(segment_text)
        words = None
        if word_timestamps and getattr(segment, "words", None):
            words = [
                TranscriptionWord(
                    word=word.word,
                    start=word.start,
                    end=word.end,
                    probability=getattr(word, "probability", None),
                )
                for word in segment.words
            ]
        segments.append(
            TranscriptionSegment(
                id=index,
                start=float(segment.start),
                end=float(segment.end),
                text=segment_text,
                words=words,
            )
        )

    return TranscriptionResult(
        text=" ".join(part for part in text_parts if part).strip(),
        language=getattr(info, "language", None),
        duration=getattr(info, "duration", None),
        segments=segments,
    )


def format_timestamp(seconds: float, sep: str = ",") -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def format_transcription(result: TranscriptionResult, response_format: str) -> str | dict[str, Any]:
    if response_format == "text":
        return result.text
    if response_format == "json":
        return result.to_dict(verbose=False)
    if response_format == "verbose_json":
        return result.to_dict(verbose=True)
    if response_format == "srt":
        return export_subtitle(from_transcription_result(result), "srt")
    if response_format == "vtt":
        return export_subtitle(from_transcription_result(result), "vtt")
    raise ValueError(f"Unsupported transcription format: {response_format}")


def transcribe_for_ui(
    audio_path,
    model_id,
    language,
    device,
    compute_type,
    word_timestamps,
    beam_size,
    response_format,
):
    if not audio_path:
        return "", "Please upload an audio file.", {}
    try:
        result = transcribe_file(
            audio_path=audio_path,
            model_id=model_id or DEFAULT_ASR_MODEL_ID,
            language=language or None,
            device=device or None,
            compute_type=compute_type or None,
            word_timestamps=bool(word_timestamps),
            beam_size=int(beam_size or 5),
        )
        formatted = format_transcription(result, response_format or "verbose_json")
    except Exception as e:
        return "", f"Error: {type(e).__name__}: {e}", {}

    if isinstance(formatted, dict):
        text_output = formatted.get("text", "")
        json_output = formatted
    else:
        text_output = formatted
        json_output = result.to_dict(verbose=True)
    return text_output, "Done.", json_output
