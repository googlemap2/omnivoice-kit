import sys

from backend.mcp import server as _server

sys.modules[__name__] = _server
