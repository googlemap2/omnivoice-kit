import importlib
import sys

_module = importlib.import_module("voicekit.infrastructure.database")
sys.modules[__name__] = _module
