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
