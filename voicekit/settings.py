import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from voicekit.audio import EFFECT_PRESETS
from voicekit.model_store import DEFAULT_MODEL_ID


DEFAULT_TRANSLATION_PROVIDER = "passthrough"
KNOWN_TRANSLATION_PROVIDER_IDS = {
    "passthrough",
    "nllb",
    "google",
    "deepl",
    "microsoft",
    "mymemory",
}

DEFAULT_NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"


DEFAULT_SETTINGS_PATH = Path("data") / "settings.json"


@dataclass(frozen=True)
class AppSettings:
    default_model: str = DEFAULT_MODEL_ID
    default_device: str | None = None
    default_effect_preset: str = "raw"
    output_dir: str = "outputs"
    default_translation_provider: str = DEFAULT_TRANSLATION_PROVIDER
    translation_provider_config: dict[str, Any] = field(default_factory=dict)
    huggingface_token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SettingsStore:
    def __init__(self, path: str | Path = DEFAULT_SETTINGS_PATH):
        self.path = Path(path)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return AppSettings()
        if not isinstance(raw, dict):
            return AppSettings()
        return self._normalize(raw)

    def save(self, settings: AppSettings) -> AppSettings:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized = self._normalize(settings.to_dict())
        self.path.write_text(json.dumps(normalized.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
        return normalized

    def update(self, **updates) -> AppSettings:
        current = self.load().to_dict()
        for key, value in updates.items():
            if value is not None:
                current[key] = value
        return self.save(self._normalize(current))

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> AppSettings:
        default_model = str(raw.get("default_model") or DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID
        default_device = raw.get("default_device")
        if default_device == "":
            default_device = None
        if default_device is not None:
            default_device = str(default_device).strip().lower() or None
        if default_device not in {None, "cpu", "cuda", "mps"}:
            default_device = None

        effect = str(raw.get("default_effect_preset") or "raw").strip().lower()
        if effect not in EFFECT_PRESETS:
            effect = "raw"

        output_dir = str(raw.get("output_dir") or "outputs").strip() or "outputs"

        translation_provider = str(
            raw.get("default_translation_provider") or DEFAULT_TRANSLATION_PROVIDER
        ).strip().lower() or DEFAULT_TRANSLATION_PROVIDER
        if translation_provider not in KNOWN_TRANSLATION_PROVIDER_IDS:
            translation_provider = DEFAULT_TRANSLATION_PROVIDER

        provider_config = raw.get("translation_provider_config")
        if not isinstance(provider_config, dict):
            provider_config = {}

        huggingface_token = raw.get("huggingface_token")
        if huggingface_token is not None:
            huggingface_token = str(huggingface_token).strip() or None

        return AppSettings(
            default_model=default_model,
            default_device=default_device,
            default_effect_preset=effect,
            output_dir=output_dir,
            default_translation_provider=translation_provider,
            translation_provider_config=provider_config,
            huggingface_token=huggingface_token,
        )


def get_settings_store() -> SettingsStore:
    return SettingsStore()


def load_settings() -> AppSettings:
    return get_settings_store().load()


def save_settings(settings: AppSettings) -> AppSettings:
    return get_settings_store().save(settings)


def _provider_cfg(config: dict[str, Any] | None, provider: str) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    raw = config.get(provider)
    return raw if isinstance(raw, dict) else {}


def get_translation_provider_field(
    settings: AppSettings | None,
    provider: str,
    field: str,
    default: Any = "",
) -> Any:
    settings = settings or load_settings()
    value = _provider_cfg(settings.translation_provider_config, provider).get(field, default)
    return default if value is None else value


def merge_translation_provider_config(
    base: dict[str, Any] | None,
    *,
    google_api_key: str | None = None,
    google_disabled: bool | None = None,
    deepl_api_key: str | None = None,
    microsoft_api_key: str | None = None,
    microsoft_region: str | None = None,
    mymemory_api_key: str | None = None,
    nllb_model_id: str | None = None,
) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base) if isinstance(base, dict) else {}

    def patch(provider: str, updates: dict[str, Any]) -> None:
        current = dict(_provider_cfg(merged, provider))
        current.update(updates)
        merged[provider] = current

    if google_api_key is not None or google_disabled is not None:
        patch(
            "google",
            {
                **({"api_key": str(google_api_key).strip()} if google_api_key is not None else {}),
                **({"disabled": bool(google_disabled)} if google_disabled is not None else {}),
            },
        )
    if deepl_api_key is not None:
        patch("deepl", {"api_key": str(deepl_api_key).strip()})
    if microsoft_api_key is not None or microsoft_region is not None:
        patch(
            "microsoft",
            {
                **({"api_key": str(microsoft_api_key).strip()} if microsoft_api_key is not None else {}),
                **({"region": str(microsoft_region).strip()} if microsoft_region is not None else {}),
            },
        )
    if mymemory_api_key is not None:
        patch("mymemory", {"api_key": str(mymemory_api_key).strip()})
    if nllb_model_id is not None:
        model_id = str(nllb_model_id).strip() or DEFAULT_NLLB_MODEL_ID
        patch("nllb", {"model_id": model_id})

    return merged
