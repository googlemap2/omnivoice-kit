import importlib
import sys

_module = importlib.import_module("voicekit.services.speech_service")
sys.modules[__name__] = _module
