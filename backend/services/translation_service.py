from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

from backend.infrastructure.model_store import ensure_local_model
from backend.stores.provider_models import get_provider_model_store
from backend.domain.settings import DEFAULT_TRANSLATION_PROVIDER, AppSettings, load_settings

TRANSLATION_LANGUAGE_CHOICES = [
    ("Vietnamese (vi)", "vi"),
    ("English (en)", "en"),
    ("Chinese (zh)", "zh"),
    ("Japanese (ja)", "ja"),
    ("Korean (ko)", "ko"),
    ("French (fr)", "fr"),
    ("German (de)", "de"),
    ("Spanish (es)", "es"),
    ("Russian (ru)", "ru"),
    ("Thai (th)", "th"),
    ("Indonesian (id)", "id"),
    ("Auto Detect", ""),
]


@dataclass(frozen=True)
class TranslationSegment:
    id: int
    text: str
    start: float | None = None
    end: float | None = None
    translated_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_language: str | None
    target_language: str | None
    provider: str
    segments: list[TranslationSegment] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "text": self.text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "provider": self.provider,
        }
        if self.segments is not None:
            data["segments"] = [segment.to_dict() for segment in self.segments]
        return data


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    name: str
    provider_type: str
    available: bool
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TranslationProvider(ABC):
    provider_id: str
    display_name: str
    provider_type: str

    @abstractmethod
    def availability(self, settings: AppSettings) -> tuple[bool, str | None]:
        pass

    @abstractmethod
    def list_languages(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def translate_text(
        self,
        text: str,
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> str:
        pass

    def translate_segments(
        self,
        segments: list[TranslationSegment],
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> list[TranslationSegment]:
        translated: list[TranslationSegment] = []
        for segment in segments:
            translated_text = self.translate_text(
                segment.text,
                source_language=source_language,
                target_language=target_language,
                settings=settings,
            )
            translated.append(
                TranslationSegment(
                    id=segment.id,
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    translated_text=translated_text,
                    metadata=dict(segment.metadata),
                )
            )
        return translated


class PassthroughProvider(TranslationProvider):
    provider_id = "passthrough"
    display_name = "Passthrough (no translation)"
    provider_type = "offline"

    def availability(self, settings: AppSettings) -> tuple[bool, str | None]:
        return True, None

    def list_languages(self) -> list[dict[str, str]]:
        return [{"id": code, "label": label} for label, code in TRANSLATION_LANGUAGE_CHOICES if code]

    def translate_text(
        self,
        text: str,
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> str:
        return text.strip()


class NLLBProvider(TranslationProvider):
    provider_id = "nllb"
    display_name = "NLLB-200 (local)"
    provider_type = "offline"
    _model = None
    _tokenizer = None

    def availability(self, settings: AppSettings) -> tuple[bool, str | None]:
        try:
            import transformers  # noqa: F401
        except ImportError:
            return False, "Install transformers to use NLLB: uv add transformers"
        config = (settings.translation_provider_config or {}).get(self.provider_id) or {}
        if config.get("disabled"):
            return False, "NLLB provider is disabled in settings."
        return True, "Requires model download on first use."

    def list_languages(self) -> list[dict[str, str]]:
        return [{"id": code, "label": label} for label, code in TRANSLATION_LANGUAGE_CHOICES if code]

    def _load(self, settings: AppSettings):
        if self._model is not None and self._tokenizer is not None:
            return
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as e:
            raise RuntimeError("Missing dependency 'transformers'. Run `uv add transformers`.") from e

        config = (settings.translation_provider_config or {}).get(self.provider_id) or {}
        model_id = str(config.get("model_id") or "facebook/nllb-200-distilled-600M")
        local_path = ensure_local_model(model_id)
        self._tokenizer = AutoTokenizer.from_pretrained(local_path)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(local_path)

    @staticmethod
    def _flores_code(language: str | None) -> str:
        if not language:
            return "eng_Latn"
        mapping = {
            "en": "eng_Latn",
            "vi": "vie_Latn",
            "zh": "zho_Hans",
            "ja": "jpn_Jpan",
            "ko": "kor_Hang",
            "fr": "fra_Latn",
            "de": "deu_Latn",
            "es": "spa_Latn",
            "ru": "rus_Cyrl",
            "th": "tha_Thai",
            "id": "ind_Latn",
        }
        return mapping.get(language.strip().lower(), "eng_Latn")

    def translate_text(
        self,
        text: str,
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> str:
        if not text.strip():
            return ""
        if not target_language:
            raise ValueError("target_language is required for NLLB translation.")

        self._load(settings)
        assert self._tokenizer is not None and self._model is not None

        src = self._flores_code(source_language)
        tgt = self._flores_code(target_language)
        self._tokenizer.src_lang = src
        inputs = self._tokenizer(text.strip(), return_tensors="pt")
        forced_bos = self._tokenizer.convert_tokens_to_ids(tgt)
        outputs = self._model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=512)
        return self._tokenizer.batch_decode(outputs, skip_special_tokens=True)[0].strip()


class _OnlinePlaceholderProvider(TranslationProvider):
    def __init__(self, provider_id: str, display_name: str, config_key: str, setup_hint: str):
        self.provider_id = provider_id
        self.display_name = display_name
        self.provider_type = "online"
        self.config_key = config_key
        self.setup_hint = setup_hint

    def _config(self, settings: AppSettings) -> dict[str, Any]:
        raw = (settings.translation_provider_config or {}).get(self.config_key)
        return raw if isinstance(raw, dict) else {}

    def availability(self, settings: AppSettings) -> tuple[bool, str | None]:
        config = self._config(settings)
        if self.config_key == "microsoft":
            if config.get("api_key") and config.get("region"):
                return True, None
            return False, self.setup_hint
        if config.get("api_key"):
            return True, None
        return False, self.setup_hint

    def list_languages(self) -> list[dict[str, str]]:
        return [{"id": code, "label": label} for label, code in TRANSLATION_LANGUAGE_CHOICES if code]

    def translate_text(
        self,
        text: str,
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> str:
        available, message = self.availability(settings)
        if not available:
            raise RuntimeError(message or f"{self.display_name} is not configured.")
        raise NotImplementedError(f"{self.display_name} adapter is not implemented yet.")


def _normalize_lang_code(language: str | None, *, allow_auto: bool = False) -> str:
    if language is None or not str(language).strip():
        return "auto" if allow_auto else ""
    code = str(language).strip().lower()
    aliases = {
        "zh": "zh-CN",
        "chinese": "zh-CN",
        "chinese (zh)": "zh-CN",
    }
    if code in aliases:
        return aliases[code]
    return code.split("_")[0].split("-")[0]


class GoogleTranslateProvider(TranslationProvider):
    provider_id = "google"
    display_name = "Google Translate"
    provider_type = "online"

    def _config(self, settings: AppSettings) -> dict[str, Any]:
        raw = (settings.translation_provider_config or {}).get("google")
        return raw if isinstance(raw, dict) else {}

    def availability(self, settings: AppSettings) -> tuple[bool, str | None]:
        try:
            import deep_translator  # noqa: F401
        except ImportError:
            return False, "Install deep-translator: uv add deep-translator"
        if self._config(settings).get("disabled"):
            return False, "Google Translate is disabled in settings."
        return True, "Uses Google Translate via deep-translator (no API key required)."

    def list_languages(self) -> list[dict[str, str]]:
        return [{"id": code, "label": label} for label, code in TRANSLATION_LANGUAGE_CHOICES if code]

    def translate_text(
        self,
        text: str,
        source_language: str | None,
        target_language: str | None,
        settings: AppSettings,
    ) -> str:
        available, message = self.availability(settings)
        if not available:
            raise RuntimeError(message or "Google Translate is not available.")

        if not text.strip():
            return ""
        if not target_language or not str(target_language).strip():
            raise ValueError("target_language is required for Google Translate.")

        try:
            from deep_translator import GoogleTranslator
        except ImportError as e:
            raise RuntimeError("Install deep-translator: uv add deep-translator") from e

        source = _normalize_lang_code(source_language, allow_auto=True) or "auto"
        target = _normalize_lang_code(target_language)
        if not target:
            raise ValueError("target_language is required for Google Translate.")
        if target == "auto":
            raise ValueError("target_language cannot be auto for Google Translate.")

        translator = GoogleTranslator(source=source, target=target)
        return translator.translate(text.strip())


class DeepLProvider(_OnlinePlaceholderProvider):
    def __init__(self) -> None:
        super().__init__(
            "deepl",
            "DeepL",
            "deepl",
            "Set translation_provider_config.deepl.api_key in settings.",
        )


class MicrosoftTranslatorProvider(_OnlinePlaceholderProvider):
    def __init__(self) -> None:
        super().__init__(
            "microsoft",
            "Microsoft Translator",
            "microsoft",
            "Set translation_provider_config.microsoft.api_key and region in settings.",
        )


class MyMemoryProvider(_OnlinePlaceholderProvider):
    def __init__(self) -> None:
        super().__init__(
            "mymemory",
            "MyMemory",
            "mymemory",
            "Set translation_provider_config.mymemory.api_key in settings (optional for limited use).",
        )


_PROVIDERS: dict[str, TranslationProvider] = {
    PassthroughProvider.provider_id: PassthroughProvider(),
    NLLBProvider.provider_id: NLLBProvider(),
    GoogleTranslateProvider().provider_id: GoogleTranslateProvider(),
    DeepLProvider().provider_id: DeepLProvider(),
    MicrosoftTranslatorProvider().provider_id: MicrosoftTranslatorProvider(),
    MyMemoryProvider().provider_id: MyMemoryProvider(),
}


def list_provider_ids() -> list[str]:
    return list(_PROVIDERS.keys())


def get_provider(provider_id: str | None) -> TranslationProvider:
    chosen = (provider_id or DEFAULT_TRANSLATION_PROVIDER).strip().lower()
    provider = _PROVIDERS.get(chosen)
    if provider is None:
        raise KeyError(f"Unknown translation provider: {provider_id}")
    return provider


def list_providers(settings: AppSettings | None = None) -> list[ProviderInfo]:
    settings = settings or load_settings()
    items: list[ProviderInfo] = []
    for provider in _PROVIDERS.values():
        available, message = provider.availability(settings)
        items.append(
            ProviderInfo(
                id=provider.provider_id,
                name=provider.display_name,
                provider_type=provider.provider_type,
                available=available,
                message=message,
            )
        )
    return items


def normalize_segments(raw_segments: list[dict[str, Any]] | None) -> list[TranslationSegment]:
    if not raw_segments:
        return []
    segments: list[TranslationSegment] = []
    for index, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        seg_id = item.get("id", index)
        try:
            seg_id = int(seg_id)
        except (TypeError, ValueError):
            seg_id = index
        start = item.get("start")
        end = item.get("end")
        segments.append(
            TranslationSegment(
                id=seg_id,
                text=text,
                start=float(start) if start is not None else None,
                end=float(end) if end is not None else None,
                translated_text=item.get("translated_text"),
                metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
            )
        )
    return segments


def translate_text(
    text: str,
    source_language: str | None = None,
    target_language: str | None = None,
    provider_id: str | None = None,
    settings: AppSettings | None = None,
) -> TranslationResult:
    settings = settings or load_settings()
    provider = get_provider(provider_id or settings.default_translation_provider)
    available, message = provider.availability(settings)
    if not available:
        raise RuntimeError(message or f"Provider '{provider.provider_id}' is not available.")

    translated = provider.translate_text(
        text=text,
        source_language=source_language or None,
        target_language=target_language or None,
        settings=settings,
    )
    return TranslationResult(
        text=translated,
        source_language=source_language or None,
        target_language=target_language or None,
        provider=provider.provider_id,
    )


def translate_segments(
    segments: list[TranslationSegment] | list[dict[str, Any]],
    source_language: str | None = None,
    target_language: str | None = None,
    provider_id: str | None = None,
    settings: AppSettings | None = None,
) -> TranslationResult:
    settings = settings or load_settings()
    provider = get_provider(provider_id or settings.default_translation_provider)
    available, message = provider.availability(settings)
    if not available:
        raise RuntimeError(message or f"Provider '{provider.provider_id}' is not available.")

    normalized = (
        segments
        if segments and isinstance(segments[0], TranslationSegment)
        else normalize_segments(segments)  # type: ignore[arg-type]
    )
    if not normalized:
        raise ValueError("segments must not be empty.")

    translated_segments = provider.translate_segments(
        normalized,
        source_language=source_language or None,
        target_language=target_language or None,
        settings=settings,
    )
    combined = " ".join(
        (segment.translated_text or "").strip()
        for segment in translated_segments
        if (segment.translated_text or "").strip()
    ).strip()
    return TranslationResult(
        text=combined,
        source_language=source_language or None,
        target_language=target_language or None,
        provider=provider.provider_id,
        segments=translated_segments,
    )


def _provider_model_chat_completion(
    provider_model_id: str,
    messages: list[dict[str, str]],
    *,
    model_name: str | None = None,
) -> str:
    record = get_provider_model_store().get_provider_model(provider_model_id)
    if record is None:
        raise ValueError(f"Provider model not found: {provider_model_id}")
    base_url = record.base_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("Provider model base_url is required.")

    config = record.config or {}
    available_models = config.get("available_models")
    selected_model = (
        (model_name or "").strip()
        or str(config.get("translation_model") or "").strip()
        or str(config.get("chat_model") or "").strip()
        or (available_models[0] if isinstance(available_models, list) and available_models else "")
        or (record.transcription_model or "")
        or (record.speech_model or "")
    )
    if not selected_model:
        raise ValueError("Provider model has no available chat model. Execute model discovery or choose a model.")

    headers = {"Content-Type": "application/json"}
    if record.api_key:
        headers["Authorization"] = f"Bearer {record.api_key}"
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={
            "model": selected_model,
            "messages": messages,
            "temperature": 0.2,
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Provider model returned an empty translation.")
    return content.strip()


def translate_segments_with_provider_model(
    segments: list[TranslationSegment] | list[dict[str, Any]],
    source_language: str | None = None,
    target_language: str | None = None,
    provider_model_id: str | None = None,
    provider_model_name: str | None = None,
) -> TranslationResult:
    if not provider_model_id:
        raise ValueError("provider_model_id is required.")
    if not target_language:
        raise ValueError("target_language is required for model-provider translation.")

    normalized = (
        segments
        if segments and isinstance(segments[0], TranslationSegment)
        else normalize_segments(segments)  # type: ignore[arg-type]
    )
    if not normalized:
        raise ValueError("segments must not be empty.")

    payload = [
        {
            "id": segment.id,
            "text": segment.text,
        }
        for segment in normalized
    ]
    content = _provider_model_chat_completion(
        provider_model_id,
        [
            {
                "role": "system",
                "content": (
                    "Translate subtitle segments. Return only a JSON array where each item has "
                    "id and translated_text. Preserve item count, ids, meaning, names, numbers, "
                    "and subtitle line brevity. Do not add commentary."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "source_language": source_language or "auto",
                        "target_language": target_language,
                        "segments": payload,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        model_name=provider_model_name,
    )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("[")
        end = content.rfind("]")
        if start < 0 or end < start:
            raise
        parsed = json.loads(content[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("Provider model translation response must be a JSON array.")

    by_id: dict[int, str] = {}
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            item_id = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        translated_text = str(item.get("translated_text") or item.get("text") or "").strip()
        if translated_text:
            by_id[item_id] = translated_text

    translated_segments = [
        TranslationSegment(
            id=segment.id,
            text=segment.text,
            start=segment.start,
            end=segment.end,
            translated_text=by_id.get(segment.id, segment.text),
            metadata=dict(segment.metadata),
        )
        for segment in normalized
    ]
    combined = " ".join((segment.translated_text or "").strip() for segment in translated_segments).strip()
    return TranslationResult(
        text=combined,
        source_language=source_language or None,
        target_language=target_language or None,
        provider=f"provider-model:{provider_model_id}",
        segments=translated_segments,
    )


def translate_text_with_provider_model(
    text: str,
    source_language: str | None = None,
    target_language: str | None = None,
    provider_model_id: str | None = None,
    provider_model_name: str | None = None,
) -> TranslationResult:
    result = translate_segments_with_provider_model(
        [{"id": 0, "text": text}],
        source_language=source_language,
        target_language=target_language,
        provider_model_id=provider_model_id,
        provider_model_name=provider_model_name,
    )
    return TranslationResult(
        text=result.segments[0].translated_text if result.segments else result.text,
        source_language=result.source_language,
        target_language=result.target_language,
        provider=result.provider,
    )


def translate_for_ui(
    text: str,
    source_language: str,
    target_language: str,
    provider_id: str,
    segments_json: dict | list | None,
):
    try:
        segments_raw = None
        if segments_json:
            if isinstance(segments_json, dict):
                segments_raw = segments_json.get("segments")
            elif isinstance(segments_json, list):
                segments_raw = segments_json

        if segments_raw:
            result = translate_segments(
                segments=segments_raw,
                source_language=source_language or None,
                target_language=target_language or None,
                provider_id=provider_id or None,
            )
        else:
            if not text or not str(text).strip():
                return "", "Please enter text or provide segments JSON.", {}
            result = translate_text(
                text=str(text),
                source_language=source_language or None,
                target_language=target_language or None,
                provider_id=provider_id or None,
            )
    except Exception as e:
        return "", f"Error: {type(e).__name__}: {e}", {}

    return result.text, "Done.", result.to_dict()
