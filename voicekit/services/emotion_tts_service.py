import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from voicekit.audio import EFFECT_PRESETS, apply_effect_preset
from voicekit.core import get_profile_store, load_model, load_voice_clone_prompt


DEFAULT_TAG_ALIASES = {
    "whisper": "whisper",
    "excited": "high pitch",
    "surprised": "very high pitch",
    "thoughtful": "moderate pitch",
    "laughing": "high pitch",
    "chuckles": "high pitch",
}

TAG_PATTERN = re.compile(r"(\[[^\]]+\]|\([^)]+\))")


@dataclass
class TaggedSegment:
    text: str
    tag: str | None


def _normalize_tag(raw: str) -> str:
    tag = raw.strip().lower()
    if tag.startswith("[") and tag.endswith("]"):
        tag = tag[1:-1].strip().lower()
    if tag.startswith("(") and tag.endswith(")"):
        tag = tag[1:-1].strip().lower()
    return tag


def parse_tagged_script(script_text: str, default_tag: str | None = None) -> list[TaggedSegment]:
    parts = TAG_PATTERN.split(script_text)
    segments: list[TaggedSegment] = []
    current_tag = default_tag.strip() if default_tag else None

    for part in parts:
        if not part:
            continue
        stripped = part.strip()
        if not stripped:
            continue
        if TAG_PATTERN.fullmatch(stripped):
            current_tag = _normalize_tag(stripped)
            continue
        segments.append(TaggedSegment(text=stripped, tag=current_tag))
    return segments


def _resolve_instruct(tag: str | None, tag_aliases: dict[str, str], default_instruct: str | None) -> str | None:
    if tag is None:
        return default_instruct
    mapped = tag_aliases.get(tag.lower(), tag)
    return mapped.strip() if mapped else default_instruct


def run_emotion_tts_speaker_id(
    *,
    script_text: str,
    output_path: str,
    speaker_id: str,
    speakers_path: str,
    model_id: str,
    language: str | None,
    default_instruct: str | None,
    tag_aliases: dict[str, str],
    num_step: int,
    guidance_scale: float,
    speed: float,
    duration: float | None,
    denoise: bool,
    preprocess_prompt: bool,
    postprocess_output: bool,
    effect_preset: str,
    device: str | None,
    gap_ms: int,
) -> dict:
    result = render_emotion_tts_speaker_id(
        script_text=script_text,
        speaker_id=speaker_id,
        speakers_path=speakers_path,
        model_id=model_id,
        language=language,
        default_instruct=default_instruct,
        tag_aliases=tag_aliases,
        num_step=num_step,
        guidance_scale=guidance_scale,
        speed=speed,
        duration=duration,
        denoise=denoise,
        preprocess_prompt=preprocess_prompt,
        postprocess_output=postprocess_output,
        effect_preset=effect_preset,
        device=device,
        gap_ms=gap_ms,
    )
    sf.write(output_path, result["audio"], result["sample_rate"])
    return {
        "output": output_path,
        "sample_rate": result["sample_rate"],
        "segments": result["segments"],
        "tag_aliases": result["tag_aliases"],
    }


def render_emotion_tts_speaker_id(
    *,
    script_text: str,
    speaker_id: str,
    speakers_path: str,
    model_id: str,
    language: str | None,
    default_instruct: str | None,
    tag_aliases: dict[str, str],
    num_step: int,
    guidance_scale: float,
    speed: float,
    duration: float | None,
    denoise: bool,
    preprocess_prompt: bool,
    postprocess_output: bool,
    effect_preset: str,
    device: str | None,
    gap_ms: int,
) -> dict:
    if effect_preset not in EFFECT_PRESETS:
        raise ValueError(f"Unsupported effect preset: {effect_preset}")
    if not script_text.strip():
        raise ValueError("Script text is empty.")

    profile = get_profile_store(speakers_path).get_profile(speaker_id)
    if profile is None:
        raise KeyError(f"speaker_id '{speaker_id}' not found in {speakers_path}")
    voice_clone_prompt = load_voice_clone_prompt(Path(profile.prompt_path))
    chosen_language = language.strip() if language else profile.language

    segments = parse_tagged_script(script_text=script_text, default_tag=None)
    if not segments:
        raise ValueError("No text segments were found after parsing tags.")

    model = load_model(model_id, device)
    sample_rate = int(model.sampling_rate)
    gap_samples = int(max(gap_ms, 0) * sample_rate / 1000)
    gap_audio = np.zeros(gap_samples, dtype=np.float32) if gap_samples > 0 else None

    rendered: list[np.ndarray] = []
    debug_segments: list[dict] = []
    for idx, segment in enumerate(segments):
        instruct = _resolve_instruct(segment.tag, tag_aliases, default_instruct)
        audio = model.generate(
            text=segment.text,
            language=chosen_language,
            voice_clone_prompt=voice_clone_prompt,
            instruct=instruct,
            num_step=num_step,
            guidance_scale=guidance_scale,
            speed=speed,
            duration=duration,
            denoise=denoise,
            preprocess_prompt=preprocess_prompt,
            postprocess_output=postprocess_output,
        )[0]
        audio = apply_effect_preset(audio, effect_preset).astype(np.float32)
        rendered.append(audio)
        if gap_audio is not None and idx < len(segments) - 1:
            rendered.append(gap_audio)
        debug_segments.append(
            {
                "index": idx,
                "tag": segment.tag,
                "instruct": instruct,
                "text": segment.text,
                "samples": int(audio.shape[0]),
            }
        )

    merged = np.concatenate(rendered, axis=0) if rendered else np.zeros(1, dtype=np.float32)
    return {
        "sample_rate": sample_rate,
        "audio": merged,
        "segments": debug_segments,
        "tag_aliases": tag_aliases,
    }


def load_tag_aliases(tag_map_path: str | None) -> dict[str, str]:
    aliases = dict(DEFAULT_TAG_ALIASES)
    if not tag_map_path:
        return aliases
    raw = json.loads(Path(tag_map_path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("--tag-map must point to a JSON object, e.g. {\"excited\":\"high pitch\"}.")
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Tag map keys and values must be strings.")
        aliases[key.strip().lower()] = value.strip()
    return aliases
