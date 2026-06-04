import importlib
import sys

_module = importlib.import_module("backend.domain.settings")
sys.modules[__name__] = _module
