import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).parent / "omnivoice" / "clone_tts_with_speaker_id.py"), run_name="__main__")
