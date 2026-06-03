import importlib
import sys

_module = importlib.import_module("voicekit.services.emotion_tts_service")
sys.modules[__name__] = _module
