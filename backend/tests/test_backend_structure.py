from fastapi.testclient import TestClient


def test_api_entrypoint_registers_core_routes():
    from backend.app.main import app

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    paths = {route.path for route in app.routes}
    assert "/v1/audio/transcriptions" in paths
    assert "/v1/audio/speech" in paths
    assert "/v1/settings" in paths


def test_compatibility_entrypoints_import():
    from backend.cli import main as cli_main
    from backend.mcp.server import main as mcp_main
    from backend.legacy.ui import main as ui_main

    assert callable(cli_main)
    assert callable(mcp_main)
    assert callable(ui_main)

