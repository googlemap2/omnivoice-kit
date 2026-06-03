import importlib
import sys

_module = importlib.import_module("voicekit.infrastructure.model_store")
sys.modules[__name__] = _module
