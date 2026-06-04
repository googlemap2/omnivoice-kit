import importlib
import sys

_module = importlib.import_module("backend.infrastructure.media")
sys.modules[__name__] = _module
