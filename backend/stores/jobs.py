import importlib
import sys

_module = importlib.import_module("backend.infrastructure.stores.jobs")
sys.modules[__name__] = _module
