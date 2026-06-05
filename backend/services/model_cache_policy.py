from __future__ import annotations

import os


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def keep_models_loaded() -> bool:
    return _env_bool("VOICEKIT_KEEP_MODELS_LOADED", False)


def should_cache_model(feature: str) -> bool:
    feature_key = feature.strip().lower().replace("-", "_")
    env_name = f"VOICEKIT_CACHE_{feature_key.upper()}"
    return _env_bool(env_name, keep_models_loaded())


def cache_policy_snapshot() -> dict[str, bool]:
    return {
        "keep_models_loaded": keep_models_loaded(),
        "tts": should_cache_model("tts"),
        "emotion_tts": should_cache_model("emotion_tts"),
    }
