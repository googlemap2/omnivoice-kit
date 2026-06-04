import importlib
import sys

_module = importlib.import_module("backend.domain.audio")
sys.modules[__name__] = _module
