from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SUBTITLE_FORMATS = ["srt", "vtt"]
_TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)


@dataclass(frozen=True)
class SubtitleSegment:
    id: int
    start: float
    end: float
    text: str
    speaker: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_timestamp(value: str) -> float:
    raw = value.strip().replace(",", ".")
    parts = raw.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid subtitle timestamp: {value}")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(seconds: float, sep: str = ",") -> str:
    total_ms = max(0, int(round(float(seconds) * 1000)))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def validate_segments(segments: list[SubtitleSegment], duration: float | None = None) -> list[SubtitleSegment]:
    normalized: list[SubtitleSegment] = []
    for index, segment in enumerate(sorted(segments, key=lambda item: (item.start, item.end, item.id))):
        start = max(0.0, float(segment.start))
        end = max(start, float(segment.end))
        if duration is not None:
            end = min(end, float(duration))
            start = min(start, end)
        text = segment.text.strip()
        if not text:
            continue
        normalized.append(
            SubtitleSegment(
                id=index,
                start=start,
                end=end,
                text=text,
                speaker=segment.speaker,
                metadata=dict(segment.metadata),
            )
        )
    return normalized


def normalize_segments(raw_segments: list[dict[str, Any]] | list[SubtitleSegment]) -> list[SubtitleSegment]:
    segments: list[SubtitleSegment] = []
    for index, item in enumerate(raw_segments or []):
        if isinstance(item, SubtitleSegment):
            segments.append(item)
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        start = item.get("start", 0)
        end = item.get("end", start)
        seg_id = item.get("id", index)
        try:
            seg_id = int(seg_id)
        except (TypeError, ValueError):
            seg_id = index
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        segments.append(
            SubtitleSegment(
                id=seg_id,
                start=float(start),
                end=float(end),
                text=text,
                speaker=str(item["speaker"]).strip() if item.get("speaker") else None,
                metadata=metadata,
            )
        )
    return validate_segments(segments)


def parse_srt(content: str, duration: float | None = None) -> list[SubtitleSegment]:
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").replace("\r", "\n").strip())
    segments: list[SubtitleSegment] = []
    for fallback_id, block in enumerate(blocks):
        lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        cue_id = fallback_id
        if "-->" not in lines[0]:
            try:
                cue_id = int(lines[0]) - 1
            except ValueError:
                cue_id = fallback_id
            lines = lines[1:]
        if not lines or "-->" not in lines[0]:
            continue
        match = _TIMESTAMP_RE.search(lines[0])
        if not match:
            raise ValueError(f"Invalid SRT cue timing: {lines[0]}")
        text = "\n".join(lines[1:]).strip()
        segments.append(
            SubtitleSegment(
                id=cue_id,
                start=parse_timestamp(match.group("start")),
                end=parse_timestamp(match.group("end")),
                text=text,
            )
        )
    return validate_segments(segments, duration=duration)


def parse_vtt(content: str, duration: float | None = None) -> list[SubtitleSegment]:
    text = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"^\ufeff?WEBVTT[^\n]*\n?", "", text, flags=re.IGNORECASE).strip()
    blocks = re.split(r"\n\s*\n", text)
    segments: list[SubtitleSegment] = []
    for fallback_id, block in enumerate(blocks):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].strip().upper() in {"NOTE", "STYLE", "REGION"}:
            continue
        timing_line_index = 0 if "-->" in lines[0] else 1
        if len(lines) <= timing_line_index or "-->" not in lines[timing_line_index]:
            continue
        match = _TIMESTAMP_RE.search(lines[timing_line_index])
        if not match:
            raise ValueError(f"Invalid VTT cue timing: {lines[timing_line_index]}")
        cue_id = fallback_id
        if timing_line_index == 1:
            try:
                cue_id = int(lines[0]) - 1
            except ValueError:
                cue_id = fallback_id
        cue_text = "\n".join(lines[timing_line_index + 1 :]).strip()
        segments.append(
            SubtitleSegment(
                id=cue_id,
                start=parse_timestamp(match.group("start")),
                end=parse_timestamp(match.group("end")),
                text=cue_text,
            )
        )
    return validate_segments(segments, duration=duration)


def parse_subtitle(content: str, subtitle_format: str, duration: float | None = None) -> list[SubtitleSegment]:
    fmt = subtitle_format.strip().lower().lstrip(".")
    if fmt == "srt":
        return parse_srt(content, duration=duration)
    if fmt == "vtt":
        return parse_vtt(content, duration=duration)
    raise ValueError(f"Unsupported subtitle format: {subtitle_format}")


def parse_subtitle_file(path: str | Path, subtitle_format: str | None = None) -> list[SubtitleSegment]:
    file_path = Path(path)
    fmt = subtitle_format or file_path.suffix.lstrip(".")
    return parse_subtitle(file_path.read_text(encoding="utf-8-sig"), fmt)


def export_srt(segments: list[SubtitleSegment] | list[dict[str, Any]]) -> str:
    normalized = normalize_segments(segments)  # type: ignore[arg-type]
    blocks = []
    for index, segment in enumerate(normalized, start=1):
        start = format_timestamp(segment.start, sep=",")
        end = format_timestamp(segment.end, sep=",")
        blocks.append(f"{index}\n{start} --> {end}\n{segment.text.strip()}")
    return "\n\n".join(blocks).strip() + ("\n" if blocks else "")


def export_vtt(segments: list[SubtitleSegment] | list[dict[str, Any]]) -> str:
    normalized = normalize_segments(segments)  # type: ignore[arg-type]
    blocks = ["WEBVTT", ""]
    for segment in normalized:
        start = format_timestamp(segment.start, sep=".")
        end = format_timestamp(segment.end, sep=".")
        blocks.append(f"{start} --> {end}\n{segment.text.strip()}\n")
    return "\n".join(blocks).strip() + "\n"


def export_subtitle(segments: list[SubtitleSegment] | list[dict[str, Any]], subtitle_format: str) -> str:
    fmt = subtitle_format.strip().lower().lstrip(".")
    if fmt == "srt":
        return export_srt(segments)
    if fmt == "vtt":
        return export_vtt(segments)
    raise ValueError(f"Unsupported subtitle format: {subtitle_format}")


def from_transcription_result(result: Any) -> list[SubtitleSegment]:
    raw_segments = getattr(result, "segments", [])
    segments = []
    for index, segment in enumerate(raw_segments):
        segments.append(
            SubtitleSegment(
                id=int(getattr(segment, "id", index)),
                start=float(getattr(segment, "start")),
                end=float(getattr(segment, "end")),
                text=str(getattr(segment, "text", "")).strip(),
            )
        )
    return validate_segments(segments, duration=getattr(result, "duration", None))
