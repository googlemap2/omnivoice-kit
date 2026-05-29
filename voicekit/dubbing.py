from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import soundfile as sf

from voicekit.asr import DEFAULT_ASR_MODEL_ID, transcribe_file
from voicekit.core import generate_clone_with_speaker_id
from voicekit.diarization import assign_speakers_to_segments, diarize_file
from voicekit.media import extract_audio, has_video_stream, mux_video_with_audio
from voicekit.model_store import DEFAULT_MODEL_ID
from voicekit.subtitles import export_subtitle, from_transcription_result
from voicekit.translation import translate_segments


@dataclass(frozen=True)
class DubbingResult:
    id: str
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


def dub_file(
    input_path: str | Path,
    voice: str,
    target_language: str,
    source_language: str | None = None,
    translation_provider: str | None = None,
    output_dir: str | Path = "outputs/dubbing",
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
) -> DubbingResult:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input media not found: {source}")
    if not voice:
        raise ValueError("voice is required for dubbing.")
    if not target_language:
        raise ValueError("target_language is required for dubbing.")

    job_id = uuid4().hex
    job_dir = Path(output_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

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
            model_id=diarization_model or "pyannote/speaker-diarization-3.1",
        )
        subtitle_segments = assign_speakers_to_segments(subtitle_segments, diarized)
    segment_payload = [segment.to_dict() for segment in subtitle_segments]
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

    for original, translated_segment in zip(subtitle_segments, translated_segments):
        text = (translated_segment.translated_text or translated_segment.text or "").strip()
        if not text:
            continue
        audio, status = generate_clone_with_speaker_id(
            text=text,
            speaker_id=voice,
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
            "metadata": segment.metadata,
        }
        for segment in translated_segments
    ]
    srt_path = job_dir / "dubbed.srt"
    vtt_path = job_dir / "dubbed.vtt"
    srt_path.write_text(export_subtitle(translated_subtitle_payload, "srt"), encoding="utf-8")
    vtt_path.write_text(export_subtitle(translated_subtitle_payload, "vtt"), encoding="utf-8")

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
    )
