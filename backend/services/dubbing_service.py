from __future__ import annotations

import re
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from backend.services.transcription_service import DEFAULT_ASR_MODEL_ID, transcribe_file
from backend.services.speech_service import generate_clone_with_speaker_id, get_profile_store
from backend.services.diarization_service import assign_speakers_to_segments, diarize_file
from backend.infrastructure.media import extract_audio, has_video_stream, mux_video_with_audio
from backend.infrastructure.model_store import DEFAULT_DIARIZATION_MODEL_ID, DEFAULT_MODEL_ID
from backend.services.subtitle_service import export_subtitle, from_transcription_result
from backend.services.translation_service import translate_segments, translate_segments_with_provider_model
from backend.paths import OUTPUTS_DIR


@dataclass(frozen=True)
class DubbingResult:
    id: str
    folder_name: str
    input_path: str
    extracted_audio_path: str
    dubbed_audio_path: str
    dubbed_video_path: str | None
    srt_path: str
    vtt_path: str
    segment_count: int
    source_language: str | None
    target_language: str | None
    voice: str
    speakers: list[str]
    speaker_voices: dict[str, str]
    segment_voices: list[dict[str, Any]]
    voice_manifest_path: str

    def to_dict(self) -> dict:
        return asdict(self)


def fit_audio_to_duration(samples: np.ndarray, sample_rate: int, duration: float) -> np.ndarray:
    target_len = max(0, int(round(float(duration) * sample_rate)))
    audio = np.asarray(samples, dtype=np.float32).reshape(-1)
    if target_len <= 0:
        return np.zeros(0, dtype=np.float32)
    if audio.size >= target_len:
        return audio[:target_len]
    return np.pad(audio, (0, target_len - audio.size))


def place_segment(
    timeline: np.ndarray,
    samples: np.ndarray,
    sample_rate: int,
    start: float,
    end: float,
) -> None:
    start_idx = max(0, int(round(float(start) * sample_rate)))
    end_idx = min(timeline.size, int(round(float(end) * sample_rate)))
    if end_idx <= start_idx:
        return
    fitted = fit_audio_to_duration(samples, sample_rate, (end_idx - start_idx) / sample_rate)
    timeline[start_idx:end_idx] += fitted[: end_idx - start_idx]


def sanitize_folder_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    normalized = re.sub(r"-+", "-", normalized).strip(" .-_")
    return normalized[:80] or "dubbing"


def next_output_folder(output_dir: str | Path, input_path: str | Path, folder_name: str | None = None) -> tuple[str, Path]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    source = Path(input_path)
    base_name = sanitize_folder_name(folder_name or source.stem or "dubbing")
    candidate = base_dir / base_name
    if not candidate.exists():
        candidate.mkdir(parents=True)
        return base_name, candidate
    index = 2
    while True:
        next_name = f"{base_name}-{index}"
        candidate = base_dir / next_name
        if not candidate.exists():
            candidate.mkdir(parents=True)
            return next_name, candidate
        index += 1


def normalize_speaker_voice_map(value: dict[str, Any] | None) -> dict[str, str]:
    if not value:
        return {}
    return {str(key).strip(): str(item).strip() for key, item in value.items() if str(key).strip() and str(item).strip()}


def voice_for_segment(default_voice: str, speaker: str | None, speaker_voice_map: dict[str, str]) -> str:
    if speaker and speaker in speaker_voice_map:
        return speaker_voice_map[speaker]
    return default_voice


def validate_speaker_voice_map(default_voice: str, speaker_voice_map: dict[str, str]) -> None:
    profile_store = get_profile_store()
    voice_ids = {profile.id for profile in profile_store.list_profiles()}
    missing = sorted({default_voice, *speaker_voice_map.values()} - voice_ids)
    if missing:
        raise ValueError(f"Unknown voice profile(s): {', '.join(missing)}")


def dub_file(
    input_path: str | Path,
    voice: str,
    target_language: str,
    source_language: str | None = None,
    translation_provider: str | None = None,
    provider_model_id: str | None = None,
    provider_model_name: str | None = None,
    output_dir: str | Path = OUTPUTS_DIR / "dubbing",
    folder_name: str | None = None,
    tts_model: str = DEFAULT_MODEL_ID,
    asr_model: str = DEFAULT_ASR_MODEL_ID,
    effect_preset: str = "raw",
    num_step: int = 16,
    guidance_scale: float = 2.0,
    speed: float = 1.0,
    device: str | None = None,
    enable_diarization: bool = False,
    diarization_model: str | None = None,
    hf_token: str | None = None,
    speaker_voice_map: dict[str, str] | None = None,
) -> DubbingResult:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input media not found: {source}")
    if not voice:
        raise ValueError("voice is required for dubbing.")
    if not target_language:
        raise ValueError("target_language is required for dubbing.")

    normalized_speaker_voice_map = normalize_speaker_voice_map(speaker_voice_map)
    validate_speaker_voice_map(voice, normalized_speaker_voice_map)
    job_id, job_dir = next_output_folder(output_dir, source, folder_name=folder_name)

    extracted_audio = extract_audio(source, job_dir / "source.wav")
    transcription = transcribe_file(
        audio_path=extracted_audio,
        model_id=asr_model,
        language=source_language or None,
        device=device,
    )
    subtitle_segments = from_transcription_result(transcription)
    if enable_diarization:
        diarized = diarize_file(
            extracted_audio,
            hf_token=hf_token,
            model_id=diarization_model or DEFAULT_DIARIZATION_MODEL_ID,
        )
        subtitle_segments = assign_speakers_to_segments(subtitle_segments, diarized)
    segment_payload = [segment.to_dict() for segment in subtitle_segments]
    if provider_model_id:
        translated = translate_segments_with_provider_model(
            segments=segment_payload,
            source_language=source_language or transcription.language,
            target_language=target_language,
            provider_model_id=provider_model_id,
            provider_model_name=provider_model_name,
        )
    else:
        translated = translate_segments(
            segments=segment_payload,
            source_language=source_language or transcription.language,
            target_language=target_language,
            provider_id=translation_provider,
        )
    translated_segments = translated.segments or []

    sample_rate = 24000
    duration = max((segment.end for segment in subtitle_segments), default=0.0)
    timeline = np.zeros(max(1, int(round((duration + 1.0) * sample_rate))), dtype=np.float32)
    segment_voice_manifest: list[dict[str, Any]] = []

    for original, translated_segment in zip(subtitle_segments, translated_segments):
        text = (translated_segment.translated_text or translated_segment.text or "").strip()
        if not text:
            continue
        speaker = original.speaker or original.metadata.get("speaker")
        segment_voice = voice_for_segment(voice, str(speaker) if speaker else None, normalized_speaker_voice_map)
        segment_voice_manifest.append(
            {
                "id": original.id,
                "start": original.start,
                "end": original.end,
                "speaker": str(speaker) if speaker else None,
                "voice": segment_voice,
                "text": text,
            }
        )
        audio, status = generate_clone_with_speaker_id(
            text=text,
            speaker_id=segment_voice,
            model_id=tts_model,
            language=target_language,
            instruct_items=[],
            num_step=num_step,
            guidance_scale=guidance_scale,
            speed=speed,
            duration=max(0.1, original.end - original.start),
            denoise=True,
            preprocess_prompt=True,
            postprocess_output=True,
            effect_preset=effect_preset,
            record_history=False,
        )
        if audio is None:
            raise RuntimeError(status)
        sample_rate, samples = audio
        place_segment(timeline, np.asarray(samples, dtype=np.float32) / 32767.0, sample_rate, original.start, original.end)

    timeline = np.clip(timeline, -1.0, 1.0)
    dubbed_audio = job_dir / "dubbed.wav"
    sf.write(dubbed_audio, timeline, sample_rate)

    translated_subtitle_payload = [
        {
            "id": segment.id,
            "start": segment.start,
            "end": segment.end,
            "text": segment.translated_text or segment.text,
            "speaker": segment.metadata.get("speaker") if segment.metadata else None,
            "metadata": {
                **segment.metadata,
                "voice": voice_for_segment(
                    voice,
                    str(segment.metadata.get("speaker")) if segment.metadata.get("speaker") else None,
                    normalized_speaker_voice_map,
                ),
            },
        }
        for segment in translated_segments
    ]
    srt_path = job_dir / "dubbed.srt"
    vtt_path = job_dir / "dubbed.vtt"
    voice_manifest_path = job_dir / "voice_manifest.json"
    srt_path.write_text(export_subtitle(translated_subtitle_payload, "srt"), encoding="utf-8")
    vtt_path.write_text(export_subtitle(translated_subtitle_payload, "vtt"), encoding="utf-8")
    voice_manifest_path.write_text(json.dumps(segment_voice_manifest, ensure_ascii=True, indent=2), encoding="utf-8")

    dubbed_video_path = None
    if has_video_stream(source):
        output_video = job_dir / "dubbed.mp4"
        try:
            mux_video_with_audio(source, dubbed_audio, output_video)
            dubbed_video_path = str(output_video)
        except Exception:
            dubbed_video_path = None

    return DubbingResult(
        id=job_id,
        folder_name=job_id,
        input_path=str(source),
        extracted_audio_path=str(extracted_audio),
        dubbed_audio_path=str(dubbed_audio),
        dubbed_video_path=dubbed_video_path,
        srt_path=str(srt_path),
        vtt_path=str(vtt_path),
        segment_count=len(translated_segments),
        source_language=source_language or transcription.language,
        target_language=target_language,
        voice=voice,
        speakers=sorted(
            {
                str(segment.speaker or segment.metadata.get("speaker"))
                for segment in subtitle_segments
                if segment.speaker or segment.metadata.get("speaker")
            }
        ),
        speaker_voices=normalized_speaker_voice_map,
        segment_voices=segment_voice_manifest,
        voice_manifest_path=str(voice_manifest_path),
    )
