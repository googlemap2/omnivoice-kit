import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).parent / "nllb" / "translate_srt.py"), run_name="__main__")

