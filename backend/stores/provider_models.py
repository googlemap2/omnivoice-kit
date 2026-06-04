import importlib
import sys

_module = importlib.import_module("backend.infrastructure.stores.provider_models")
sys.modules[__name__] = _module
