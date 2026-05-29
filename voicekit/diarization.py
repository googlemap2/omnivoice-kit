from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from voicekit.model_store import DEFAULT_DIARIZATION_MODEL_ID, ensure_local_model
from voicekit.settings import load_settings
from voicekit.subtitles import SubtitleSegment, normalize_segments


@dataclass(frozen=True)
class DiarizationSegment:
    start: float
    end: float
    speaker: str
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_huggingface_token(token: str | None = None) -> str | None:
    if token and token.strip():
        return token.strip()
    settings_token = load_settings().huggingface_token
    if settings_token:
        return settings_token
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")


def configure_headless_matplotlib() -> None:
    backend = os.environ.get("MPLBACKEND", "").strip()
    if backend.startswith("module://") or backend == "":
        os.environ["MPLBACKEND"] = "agg"
    if "matplotlib" in sys.modules:
        try:
            import matplotlib

            matplotlib.use("agg", force=True)
        except Exception:
            pass


def is_gated_model_error(e: Exception) -> bool:
    text = f"{type(e).__name__}: {e}"
    return (
        "GatedRepoError" in text
        or "Cannot access gated repo" in text
        or "restricted and you are not in the authorized list" in text
        or "accept user conditions" in text
    )


def gated_model_message(e: Exception) -> str:
    text = str(e)
    gated_repos = [
        "pyannote/speaker-diarization-community-1",
        "pyannote/segmentation-3.0",
        DEFAULT_DIARIZATION_MODEL_ID,
    ]
    repo = next((item for item in gated_repos if item in text), DEFAULT_DIARIZATION_MODEL_ID)
    return (
        f"Cannot access gated pyannote model '{repo}'. "
        "Open the model page on Hugging Face, accept the user conditions/license, "
        "then use a Hugging Face token that has access. "
        "For diarization, accept pyannote/speaker-diarization-3.1, "
        "pyannote/segmentation-3.0, and pyannote/speaker-diarization-community-1."
    )


def diarization_availability(token: str | None = None) -> tuple[bool, str | None]:
    configure_headless_matplotlib()
    try:
        import pyannote.audio  # noqa: F401
    except ImportError:
        return False, "Install pyannote.audio to use diarization."
    if not get_huggingface_token(token):
        return False, "Set a Hugging Face token with accepted pyannote license."
    return True, None


def diarize_file(
    audio_path: str | Path,
    hf_token: str | None = None,
    model_id: str = DEFAULT_DIARIZATION_MODEL_ID,
) -> list[DiarizationSegment]:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    token = get_huggingface_token(hf_token)
    if not token:
        raise RuntimeError("Hugging Face token is required for pyannote diarization.")
    configure_headless_matplotlib()
    try:
        from pyannote.audio import Pipeline
    except ImportError as e:
        raise RuntimeError("Missing dependency 'pyannote.audio'. Install it before running diarization.") from e

    model_source = str(Path(model_id)) if Path(model_id).exists() else ensure_local_model(model_id, token=token)
    try:
        pipeline = Pipeline.from_pretrained(model_source, use_auth_token=token)
    except TypeError as e:
        if "use_auth_token" not in str(e):
            raise
        try:
            pipeline = Pipeline.from_pretrained(model_source, token=token)
        except Exception as token_error:
            if is_gated_model_error(token_error):
                raise RuntimeError(gated_model_message(token_error)) from token_error
            if not isinstance(token_error, TypeError) or "token" not in str(token_error):
                raise
            pipeline = Pipeline.from_pretrained(model_source)
    except Exception as e:
        if is_gated_model_error(e):
            raise RuntimeError(gated_model_message(e)) from e
        raise RuntimeError(
            f"Could not load {model_id}. Accept the model license on Hugging Face and verify your token."
        ) from e

    try:
        diarization = pipeline(str(path))
    except Exception as e:
        if is_gated_model_error(e):
            raise RuntimeError(gated_model_message(e)) from e
        raise
    segments: list[DiarizationSegment] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            DiarizationSegment(
                start=float(turn.start),
                end=float(turn.end),
                speaker=str(speaker),
            )
        )
    return sorted(segments, key=lambda item: (item.start, item.end, item.speaker))


def overlap_seconds(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers_to_segments(
    subtitle_segments: list[SubtitleSegment] | list[dict[str, Any]],
    diarization_segments: list[DiarizationSegment] | list[dict[str, Any]],
) -> list[SubtitleSegment]:
    normalized_subtitles = normalize_segments(subtitle_segments)  # type: ignore[arg-type]
    normalized_diarization = [
        item
        if isinstance(item, DiarizationSegment)
        else DiarizationSegment(
            start=float(item.get("start", 0)),
            end=float(item.get("end", 0)),
            speaker=str(item.get("speaker", "")),
            confidence=float(item["confidence"]) if item.get("confidence") is not None else None,
        )
        for item in diarization_segments
        if isinstance(item, DiarizationSegment) or isinstance(item, dict)
    ]

    assigned: list[SubtitleSegment] = []
    for segment in normalized_subtitles:
        best = None
        best_overlap = 0.0
        for diarized in normalized_diarization:
            current_overlap = overlap_seconds(segment.start, segment.end, diarized.start, diarized.end)
            if current_overlap > best_overlap:
                best = diarized
                best_overlap = current_overlap
        metadata = dict(segment.metadata)
        if best is not None and best_overlap > 0:
            metadata["speaker"] = best.speaker
            metadata["speaker_overlap"] = best_overlap
        assigned.append(
            SubtitleSegment(
                id=segment.id,
                start=segment.start,
                end=segment.end,
                text=segment.text,
                speaker=best.speaker if best is not None and best_overlap > 0 else segment.speaker,
                metadata=metadata,
            )
        )
    return assigned
