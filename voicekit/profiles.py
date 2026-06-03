import importlib
import sys

_module = importlib.import_module("voicekit.services.voice_profile_service")
sys.modules[__name__] = _module
