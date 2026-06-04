from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
DATA_DIR = BACKEND_ROOT / "data"
MODELS_DIR = BACKEND_ROOT / "models"
ASSETS_DIR = BACKEND_ROOT / "assets"
OUTPUTS_DIR = BACKEND_ROOT / "outputs"
SPEAKERS_PATH = BACKEND_ROOT / "speakers.json"
SPEAKERS_EXAMPLE_PATH = BACKEND_ROOT / "speakers.example.json"


def backend_path(*parts: str) -> Path:
    return BACKEND_ROOT.joinpath(*parts)


def resolve_path(path_str: str | Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p

    # Try resolving relative to BACKEND_ROOT first
    b_path = BACKEND_ROOT / p
    if b_path.exists():
        return b_path

    # Some paths in config might be from repo root, e.g. "backend/assets/..."
    if p.parts and p.parts[0] == "backend":
        b_path2 = BACKEND_ROOT.joinpath(*p.parts[1:])
        if b_path2.exists():
            return b_path2

    # Try relative to CWD
    return p.resolve()
