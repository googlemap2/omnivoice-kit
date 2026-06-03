import importlib
import sys

_module = importlib.import_module("voicekit.services.transcription_service")
sys.modules[__name__] = _module
