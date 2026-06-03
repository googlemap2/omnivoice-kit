import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voicekit.app.routers import diagnostics, files, health, meta, models, workflows
from voicekit.diagnostics import setup_logging
from voicekit.stores.jobs import get_job_worker


setup_logging()


CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://5365fbfj-3000.asse.devtunnels.ms",
    # Add your frontend/ngrok domains here, for example:
    # "https://your-frontend-domain.ngrok-free.dev",
]


def _cors_origins() -> list[str]:
    raw = os.environ.get("VOICEKIT_CORS_ORIGINS", "")
    env_origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [*CORS_ORIGINS, *env_origins]


app = FastAPI(title="OmniVoice Kit API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(meta.router)
app.include_router(models.router)
app.include_router(diagnostics.router)
app.include_router(files.router)
app.include_router(workflows.router)


@app.on_event("startup")
def start_job_worker() -> None:
    get_job_worker().start()


@app.on_event("shutdown")
def stop_job_worker() -> None:
    get_job_worker().stop()
