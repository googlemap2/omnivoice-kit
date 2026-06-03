import importlib
import sys

_module = importlib.import_module("voicekit.domain.audio")
sys.modules[__name__] = _module
