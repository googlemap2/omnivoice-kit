import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL_ID = "k2-fsa/OmniVoice"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_BASE_DIR = PROJECT_ROOT / "models"
DEFAULT_HF_HOME = PROJECT_ROOT / "models" / ".hf_home"
DEFAULT_HF_CACHE = DEFAULT_HF_HOME / "hub"
KNOWN_MODEL_IDS = [DEFAULT_MODEL_ID]


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


def configure_hf_local_cache() -> None:
    DEFAULT_HF_CACHE.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(DEFAULT_HF_HOME.resolve())
    os.environ["HF_HUB_CACHE"] = str(DEFAULT_HF_CACHE.resolve())
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(DEFAULT_HF_CACHE.resolve())
    os.environ["TRANSFORMERS_CACHE"] = str(DEFAULT_HF_CACHE.resolve())


def has_model_weights(local_dir: Path) -> bool:
    candidates = [
        local_dir / "model.safetensors",
        local_dir / "pytorch_model.bin",
        local_dir / "model.safetensors.index.json",
        local_dir / "pytorch_model.bin.index.json",
    ]
    return any(p.exists() for p in candidates)


def resolve_model_source(model_arg: str | None) -> str:
    model_name = (model_arg or DEFAULT_MODEL_ID).strip()
    path = Path(model_name)
    if path.exists():
        return str(path)
    if "/" not in model_name:
        return model_name
    return ensure_local_model(model_name)


def _repo_cache_dir(repo_id: str) -> Path:
    return DEFAULT_MODEL_BASE_DIR / f"models--{repo_id.replace('/', '--')}"


def get_model_status(repo_id: str = DEFAULT_MODEL_ID, local_dir: Path | None = None) -> ModelStatus:
    target_dir = local_dir or _repo_cache_dir(repo_id)
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
    local_dir = local_dir or _repo_cache_dir(repo_id)
    local_dir.mkdir(parents=True, exist_ok=True)
    config_file = local_dir / "config.json"
    if config_file.exists() and has_model_weights(local_dir):
        return str(local_dir)

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        cache_dir=str(DEFAULT_HF_CACHE),
    )
    return str(local_dir)
