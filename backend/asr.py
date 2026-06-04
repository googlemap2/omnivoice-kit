import importlib
import sys

_module = importlib.import_module("backend.services.transcription_service")
sys.modules[__name__] = _module
