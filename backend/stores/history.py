import importlib
import sys

_module = importlib.import_module("backend.infrastructure.stores.history")
sys.modules[__name__] = _module
