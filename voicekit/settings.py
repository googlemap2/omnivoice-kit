import importlib
import sys

_module = importlib.import_module("voicekit.domain.settings")
sys.modules[__name__] = _module
