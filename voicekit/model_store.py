import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL_ID = "k2-fsa/OmniVoice"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_BASE_DIR = PROJECT_ROOT / "models"
DEFAULT_HF_HOME = PROJECT_ROOT / "models" / ".hf_home"
DEFAULT_HF_CACHE = DEFAULT_HF_HOME / "hub"
KNOWN_MODEL_IDS = [
    DEFAULT_MODEL_ID,
    "Systran/faster-whisper-large-v3",
    "Systran/faster-whisper-large-v3-turbo",
    "Systran/faster-distil-whisper-large-v3",
    "Systran/faster-whisper-medium",
    "Systran/faster-whisper-small",
    "Systran/faster-whisper-base",
]


@dataclass(frozen=True)
class ModelStatus:
    repo_id: str
    local_path: str
    installed: bool
    config_exists: bool
    weights_exist: bool
    cache_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_models_dir() -> Path:
    """Project-local folder for downloaded model snapshots."""
    return DEFAULT_MODEL_BASE_DIR


def configure_hf_local_cache() -> None:
    """Pin Hugging Face / transformers caches under ``models/.hf_home``."""
    DEFAULT_MODEL_BASE_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_HF_HOME.mkdir(parents=True, exist_ok=True)
    DEFAULT_HF_CACHE.mkdir(parents=True, exist_ok=True)
    hf_home = str(DEFAULT_HF_HOME.resolve())
    hf_cache = str(DEFAULT_HF_CACHE.resolve())
    models_dir = str(DEFAULT_MODEL_BASE_DIR.resolve())
    os.environ["HF_HOME"] = hf_home
    os.environ["HF_HUB_CACHE"] = hf_cache
    os.environ["HUGGINGFACE_HUB_CACHE"] = hf_cache
    os.environ["TRANSFORMERS_CACHE"] = hf_cache
    os.environ["HF_DATASETS_CACHE"] = hf_cache
    # Keep all hub artifacts inside the project ``models/`` tree.
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    # Used by some libraries when resolving cache locations.
    os.environ.setdefault("VOICEKIT_MODELS_DIR", models_dir)


def has_model_weights(local_dir: Path) -> bool:
    if not local_dir.is_dir():
        return False
    candidates = [
        local_dir / "model.bin",
        local_dir / "model.safetensors",
        local_dir / "pytorch_model.bin",
        local_dir / "model.safetensors.index.json",
        local_dir / "pytorch_model.bin.index.json",
    ]
    if any(p.exists() for p in candidates):
        return True
    weight_globs = ("*.safetensors", "*.bin", "pytorch_model*.bin")
    for pattern in weight_globs:
        if any(local_dir.glob(pattern)) or any(local_dir.rglob(pattern)):
            return True
    return False


def resolve_model_source(model_arg: str | None) -> str:
    model_name = (model_arg or DEFAULT_MODEL_ID).strip()
    path = Path(model_name)
    if path.exists():
        return str(path)
    if "/" not in model_name:
        return model_name
    return ensure_local_model(model_name)


def get_local_model_dir(repo_id: str) -> Path:
    return DEFAULT_MODEL_BASE_DIR / f"models--{repo_id.replace('/', '--')}"


def get_model_status(repo_id: str = DEFAULT_MODEL_ID, local_dir: Path | None = None) -> ModelStatus:
    target_dir = local_dir or get_local_model_dir(repo_id)
    config_exists = (target_dir / "config.json").exists()
    weights_exist = has_model_weights(target_dir)
    return ModelStatus(
        repo_id=repo_id,
        local_path=str(target_dir.resolve()),
        installed=config_exists and weights_exist,
        config_exists=config_exists,
        weights_exist=weights_exist,
        cache_path=str(DEFAULT_HF_CACHE.resolve()),
    )


def list_model_statuses(repo_ids: list[str] | None = None) -> list[ModelStatus]:
    return [get_model_status(repo_id) for repo_id in (repo_ids or KNOWN_MODEL_IDS)]


def install_model(repo_id: str = DEFAULT_MODEL_ID, local_dir: Path | None = None) -> ModelStatus:
    ensure_local_model(repo_id, local_dir=local_dir)
    return get_model_status(repo_id, local_dir=local_dir)


def ensure_local_model(repo_id: str, local_dir: Path | None = None) -> str:
    configure_hf_local_cache()
    local_dir = local_dir or get_local_model_dir(repo_id)
    local_dir.mkdir(parents=True, exist_ok=True)
    if has_model_weights(local_dir):
        return str(local_dir.resolve())

    from huggingface_hub import snapshot_download

    download_kwargs: dict[str, Any] = {
        "repo_id": repo_id,
        "local_dir": str(local_dir),
    }
    try:
        snapshot_download(**download_kwargs, local_dir_only=True)
    except TypeError:
        # Older huggingface_hub: fall back to explicit project cache under models/.
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            cache_dir=str(DEFAULT_HF_CACHE),
            local_dir_use_symlinks=False,
        )
    return str(local_dir.resolve())


# Configure cache as soon as this module is imported (before any HF download).
configure_hf_local_cache()
