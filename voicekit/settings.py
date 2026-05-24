import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from voicekit.audio import EFFECT_PRESETS
from voicekit.model_store import DEFAULT_MODEL_ID


DEFAULT_SETTINGS_PATH = Path("data") / "settings.json"


@dataclass(frozen=True)
class AppSettings:
    default_model: str = DEFAULT_MODEL_ID
    default_device: str | None = None
    default_effect_preset: str = "raw"
    output_dir: str = "outputs"

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
        return AppSettings(
            default_model=default_model,
            default_device=default_device,
            default_effect_preset=effect,
            output_dir=output_dir,
        )


def get_settings_store() -> SettingsStore:
    return SettingsStore()


def load_settings() -> AppSettings:
    return get_settings_store().load()


def save_settings(settings: AppSettings) -> AppSettings:
    return get_settings_store().save(settings)
