import sys

from voicekit.mcp import server as _server

sys.modules[__name__] = _server
