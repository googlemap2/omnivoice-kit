from typing import Literal

import numpy as np


EffectPreset = Literal["raw", "normalize", "broadcast"]
EFFECT_PRESETS = ["raw", "normalize", "broadcast"]


def normalize_audio(audio, peak: float = 0.95) -> np.ndarray:
    samples = np.asarray(audio, dtype=np.float32)
    max_abs = float(np.max(np.abs(samples))) if samples.size else 0.0
    if max_abs <= 1e-8:
        return samples
    return np.clip(samples * (peak / max_abs), -1.0, 1.0)


def broadcast_audio(audio) -> np.ndarray:
    samples = np.asarray(audio, dtype=np.float32)
    if not samples.size:
        return samples

    samples = samples - float(np.mean(samples))
    rms = float(np.sqrt(np.mean(np.square(samples)))) if samples.size else 0.0
    if rms > 1e-8:
        samples = samples * min(4.0, 0.16 / rms)

    samples = np.tanh(samples * 1.35) / np.tanh(1.35)
    return normalize_audio(samples, peak=0.92)


def apply_effect_preset(audio, preset: str | None = "raw") -> np.ndarray:
    chosen = (preset or "raw").strip().lower()
    if chosen == "raw":
        return np.asarray(audio, dtype=np.float32)
    if chosen == "normalize":
        return normalize_audio(audio)
    if chosen == "broadcast":
        return broadcast_audio(audio)
    raise ValueError(f"Unsupported effect preset: {preset}")


def to_wav16(audio):
    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return wav16
