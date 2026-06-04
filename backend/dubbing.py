import importlib
import sys

_module = importlib.import_module("backend.services.dubbing_service")
sys.modules[__name__] = _module
