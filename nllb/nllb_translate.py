from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from model_store import DEFAULT_HF_CACHE, configure_hf_local_cache

DEFAULT_NLLB_MODEL_ID = "facebook/nllb-200-distilled-600M"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NLLB_MODEL_BASE_DIR = PROJECT_ROOT / "models"


@dataclass
class NllbRuntime:
    tokenizer: AutoTokenizer
    model: AutoModelForSeq2SeqLM
    device: str


_RUNTIME_CACHE: dict[tuple[str, str], NllbRuntime] = {}


def _pick_device(device_arg: str | None) -> str:
    if device_arg:
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _has_model_weights(local_dir: Path) -> bool:
    candidates = [
        local_dir / "model.safetensors",
        local_dir / "pytorch_model.bin",
        local_dir / "model.safetensors.index.json",
        local_dir / "pytorch_model.bin.index.json",
    ]
    return any(p.exists() for p in candidates)


def _resolve_model_source(model_id: str) -> str:
    maybe_path = Path(model_id)
    if maybe_path.exists():
        return str(maybe_path)

    local_dir = DEFAULT_NLLB_MODEL_BASE_DIR / model_id.replace("/", "--")
    local_dir.mkdir(parents=True, exist_ok=True)
    if (local_dir / "config.json").exists() and _has_model_weights(local_dir):
        return str(local_dir)

    snapshot_download(
        repo_id=model_id,
        local_dir=str(local_dir),
        cache_dir=str(DEFAULT_HF_CACHE.resolve()),
    )
    return str(local_dir)


def _load_runtime(model_id: str, device_arg: str | None = None) -> NllbRuntime:
    device = _pick_device(device_arg)
    key = (model_id, device)
    if key in _RUNTIME_CACHE:
        return _RUNTIME_CACHE[key]

    configure_hf_local_cache()
    model_source = _resolve_model_source(model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_source, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_source, local_files_only=True)
    if device != "cpu":
        model = model.to(device)
    model.eval()

    runtime = NllbRuntime(tokenizer=tokenizer, model=model, device=device)
    _RUNTIME_CACHE[key] = runtime
    return runtime


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    model_id: str = DEFAULT_NLLB_MODEL_ID,
    device: str | None = None,
    max_new_tokens: int = 256,
) -> str:
    if not text or not text.strip():
        return text
    runtime = _load_runtime(model_id=model_id, device_arg=device)
    tokenizer = runtime.tokenizer
    model = runtime.model

    tokenizer.src_lang = source_lang
    encoded = tokenizer(text, return_tensors="pt")
    if runtime.device != "cpu":
        encoded = {k: v.to(runtime.device) for k, v in encoded.items()}

    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)
    if forced_bos_token_id is None or forced_bos_token_id < 0:
        raise ValueError(f"Invalid NLLB target language code: {target_lang}")

    with torch.no_grad():
        generated_tokens = model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_new_tokens=max_new_tokens,
        )
    return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
