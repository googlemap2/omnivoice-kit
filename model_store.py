import os
from pathlib import Path


DEFAULT_MODEL_ID = "k2-fsa/OmniVoice"
DEFAULT_MODEL_DIR = Path("models/OmniVoice")
DEFAULT_HF_HOME = Path("models/.hf_home")
DEFAULT_HF_CACHE = DEFAULT_HF_HOME / "hub"


def configure_hf_local_cache() -> None:
    DEFAULT_HF_CACHE.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(DEFAULT_HF_HOME.resolve())
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(DEFAULT_HF_CACHE.resolve())


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


def ensure_local_model(repo_id: str, local_dir: Path = DEFAULT_MODEL_DIR) -> str:
    configure_hf_local_cache()
    local_dir.mkdir(parents=True, exist_ok=True)
    config_file = local_dir / "config.json"
    if config_file.exists() and has_model_weights(local_dir):
        return str(local_dir)

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        cache_dir=str(DEFAULT_HF_CACHE),
    )
    return str(local_dir)
