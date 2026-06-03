# Backend Structure Refactor Plan

This document tracks the approved backend folder structure refactor for `omnivoice-kit`.

The goal is to make the backend easier to navigate and extend while preserving the current API, CLI, frontend behavior, model cache paths, local data paths, and runtime workflows.

## Approved Target Structure

```text
voicekit/
  __init__.py

  app/
    __init__.py
    main.py
    dependencies.py
    errors.py
    schemas/
      speech.py
      transcription.py
      subtitles.py
      translation.py
      dubbing.py
      voices.py
      jobs.py
      settings.py
    routers/
      health.py
      meta.py
      models.py
      speech.py
      transcription.py
      subtitles.py
      translation.py
      dubbing.py
      diarization.py
      dictation.py
      jobs.py
      voices.py
      settings.py
      diagnostics.py
      files.py

  domain/
    audio.py
    speech.py
    transcription.py
    subtitles.py
    translation.py
    dubbing.py
    diarization.py
    dictation.py
    voices.py
    jobs.py
    settings.py

  services/
    speech_service.py
    transcription_service.py
    subtitle_service.py
    translation_service.py
    dubbing_service.py
    diarization_service.py
    voice_profile_service.py
    model_service.py
    diagnostics_service.py

  infrastructure/
    model_store.py
    database.py
    media.py
    logging.py
    hf.py
    stores/
      history.py
      jobs.py
      provider_models.py

  cli/
    __init__.py
    main.py
    commands/
      speech.py
      transcription.py
      subtitles.py
      translation.py
      dubbing.py
      diarization.py
      voices.py

  mcp/
    server.py
    tools.py
    resources.py

  legacy/
    ui.py
```

## Refactor Principles

- Keep behavior stable. Do not change endpoint paths, request fields, response shapes, CLI commands, output paths, or frontend contracts during structural phases.
- Move code in thin slices. Each phase must be independently verifiable before starting the next phase.
- Preserve compatibility shims until all internal imports have migrated.
- Prefer moving code over rewriting code.
- Do not refactor unrelated feature logic while moving files.
- Add tests only where the move changes import boundaries or high-risk flows.

## Validation Commands

Run the relevant checks after each phase:

```bash
python -m py_compile voicekit/api.py
uv run python -m voicekit.cli --help
uv run python -m voicekit.cli emotion-script --help
```

Frontend/API contract check:

```bash
cd frontend
pnpm build
```

Backend smoke:

```bash
uv run uvicorn voicekit.api:app --host 127.0.0.1 --port 8000
```

If `pnpm build` fails with `.next` ENOENT after a dev server was running:

```powershell
cd frontend
Remove-Item -LiteralPath .next -Recurse -Force
pnpm build
```

## Phase 0: Baseline Inventory

Status: Done

Goal: Capture the current backend entrypoints and high-risk flows before moving files.

Tasks:

- [x] List current public import entrypoints.
- [x] List FastAPI endpoints from `voicekit/api.py`.
- [x] List CLI commands from `voicekit/cli.py`.
- [x] Identify frontend calls that depend on endpoint response shapes.
- [x] Identify model/cache/data paths that must remain stable.
- [x] Record current smoke command results.

Validation:

- [x] `python -m py_compile voicekit/api.py voicekit/cli.py`
- [x] `uv run python -m voicekit.cli --help`
- [x] `cd frontend && pnpm build`

Exit criteria:

- [x] Baseline behavior and contracts are documented.
- [x] No code movement happened before baseline capture.

Baseline snapshot:

- Public backend entrypoint: `voicekit.api:app`.
- Public CLI entrypoint: `voicekit.cli:main`.
- Console scripts: `voicekit`, `voicekit-ui`, `voicekit-mcp`.
- FastAPI endpoint decorators in `voicekit/api.py`: health/meta/models/settings/diagnostics/provider-models/model-status/voices/translation/history/jobs/files/subtitles/diarization/dubbing/speech/dictation/transcription.
- CLI commands: `speaker-id`, `ref-audio`, `voice-design`, `transcribe`, `translate`, `subtitle-import`, `subtitle-export`, `dub`, `diarize`, `emotion-script`.
- Stable local paths: `models/`, `models/.hf_home/hub/`, `data/settings.json`, `data/uploads/`, `data/logs/`, `outputs/`.
- Frontend contracts remain under `/v1/*` and `/health`.

## Phase 1: App Shell

Status: Done

Goal: Create the new FastAPI app shell without changing endpoint implementations.

Tasks:

- [x] Create `voicekit/app/__init__.py`.
- [x] Create `voicekit/app/main.py`.
- [x] Move FastAPI app creation, CORS setup, logging setup, startup hook, and shutdown hook from `voicekit/api.py` to `voicekit/app/main.py`.
- [x] Keep endpoint functions in `voicekit/api.py` during this phase if that is the smallest safe move.
- [x] Keep `voicekit/api.py` as the public uvicorn entrypoint.
- [x] Ensure `uvicorn voicekit.api:app` still works through import/app smoke.

Compatibility target:

```python
from voicekit.app.main import app
```

Validation:

- [x] `python -m py_compile voicekit/api.py voicekit/app/main.py`
- [x] `uv run python -c "from voicekit.api import app; print(app.title, len(app.routes))"`
- [x] `uv run python -c "from fastapi.testclient import TestClient; from voicekit.api import app; r=TestClient(app).get('/health'); print(r.status_code, r.json())"`

Exit criteria:

- [x] `voicekit.app.main` owns the FastAPI app object.
- [x] Existing API entrypoint still works.

## Phase 2: Shared API Utilities

Status: Done

Goal: Move common API helpers into app-level support modules.

Tasks:

- [x] Create `voicekit/app/errors.py`.
- [x] Move reusable HTTP error helpers from `voicekit/api.py`.
- [x] Create `voicekit/app/dependencies.py`.
- [x] Move shared dependency/helper functions that are used by multiple routers.
- [x] Keep imports compatible with existing endpoint code.

Validation:

- [x] `python -m py_compile voicekit/api.py voicekit/app/errors.py voicekit/app/dependencies.py`
- [x] Smoke `/health`, `/v1/meta`, `/v1/model-status`.

Exit criteria:

- [x] Common API helpers are no longer embedded directly in endpoint-heavy files.

## Phase 3: Schemas

Status: Done

Goal: Move Pydantic request/response models into `voicekit/app/schemas/`.

Tasks:

- [x] Create `voicekit/app/schemas/__init__.py`.
- [x] Move speech schemas to `schemas/speech.py`.
- [x] Move transcription schemas to `schemas/transcription.py`.
- [x] Move subtitle schemas to `schemas/subtitles.py`.
- [x] Move translation schemas to `schemas/translation.py`.
- [x] Move dubbing and diarization schemas to `schemas/dubbing.py`.
- [x] Move voice profile schemas to `schemas/voices.py`.
- [x] Move job schemas to `schemas/jobs.py`.
- [x] Move settings/provider model schemas to `schemas/settings.py`.
- [x] Keep field names, defaults, validation, and enum values unchanged.

Validation:

- [x] `python -m py_compile voicekit/api.py voicekit/app/schemas/*.py`
- [x] OpenAPI route registration still succeeds on app import.
- [x] Frontend build passes.

Exit criteria:

- [x] `voicekit/api.py` no longer owns Pydantic schema definitions.
- [x] API contract remains unchanged.

## Phase 4: Routers - Low Risk

Status: Done

Goal: Move low-risk endpoints into routers first.

Tasks:

- [x] Create `voicekit/app/routers/__init__.py`.
- [x] Move `/health` into `routers/health.py`.
- [x] Move `/v1/meta`, `/v1/models`, `/v1/languages` into `routers/meta.py` or `routers/models.py`.
- [x] Move diagnostics/log endpoints into `routers/diagnostics.py`.
- [x] Move file download endpoint into `routers/files.py`.
- [x] Register routers from `voicekit/app/main.py`.

Validation:

- [x] `python -m py_compile voicekit/app/main.py voicekit/app/routers/*.py`
- [x] Smoke `/health`
- [x] Smoke `/v1/meta`
- [x] Smoke `/v1/diagnostics`

Exit criteria:

- [x] Low-risk endpoints are served by routers.
- [x] Endpoint paths and response objects remain unchanged.

## Phase 5: Routers - Core Workflows

Status: Done

Goal: Move feature endpoints into focused routers.

Tasks:

- [x] Move remaining workflow endpoints out of `voicekit/api.py`.
- [x] Register remaining workflow endpoints through `voicekit/app/routers/workflows.py`.
- [x] Keep endpoint paths, request fields, and response shapes unchanged.
- [x] Keep `voicekit/api.py` as a compatibility shim.
- [ ] Optional follow-up: split `routers/workflows.py` into focused routers (`speech.py`, `transcription.py`, `subtitles.py`, `translation.py`, `dubbing.py`, `diarization.py`, `voices.py`, `jobs.py`, `settings.py`).

Validation:

- [x] `python -m py_compile voicekit/api.py voicekit/app/main.py voicekit/app/routers/*.py`
- [x] Smoke route registration for `/v1/audio/transcriptions`.
- [x] Smoke `/v1/translation/providers`.
- [x] Smoke `/v1/jobs`.
- [x] `cd frontend && pnpm build`

Exit criteria:

- [x] `voicekit/api.py` is thin except for compatibility import.
- [x] All current endpoints are registered through routers.

## Phase 6: Services

Status: Done

Goal: Move business logic out of routers into services while keeping routers thin.

Tasks:

- [x] Create `voicekit/services/__init__.py`.
- [x] Create service modules for speech, transcription, subtitles, translation, dubbing, diarization, voices, models, and diagnostics.
- [x] Move service implementations from root modules into `voicekit/services/`.
- [x] Keep root modules as compatibility aliases.
- [x] Route workflow imports through service modules.
- [ ] Optional follow-up: move long request orchestration blocks from `routers/workflows.py` into smaller service functions.

Validation:

- [x] Python compile for all service modules.
- [x] Existing API smoke tests still pass.
- [x] Existing unit test discovery passes.
- [x] Frontend build passes.

Exit criteria:

- [x] Service package exists and is importable.
- [x] Service modules contain the real implementation for moved runtime workflows.
- [x] Service functions are reusable from API, CLI, jobs, and MCP where appropriate.
- [ ] Optional follow-up: thin `routers/workflows.py` further by moving orchestration into service functions.

## Phase 7: Infrastructure

Status: Done

Goal: Group runtime infrastructure under `voicekit/infrastructure/`.

Tasks:

- [x] Create `voicekit/infrastructure/__init__.py`.
- [x] Create Hugging Face helper facade in `infrastructure/hf.py`.
- [x] Move model store implementation into `infrastructure/model_store.py`.
- [x] Keep `voicekit/model_store.py` compatible.
- [x] Move database implementation into `infrastructure/database.py`.
- [x] Keep `voicekit/database.py` compatible.
- [x] Move media implementation into `infrastructure/media.py`.
- [x] Keep `voicekit/media.py` compatible.
- [x] Move store implementations under `infrastructure/stores/`.
- [x] Keep `voicekit/stores/*` compatible.

Validation:

- [x] Model status and install routes still import.
- [x] Hugging Face token from settings/env is still used for all `ensure_local_model()` downloads.
- [x] Dubbing still finds FFmpeg helpers through compatibility imports.
- [x] Jobs/history/provider models still find database stores.

Exit criteria:

- [x] Runtime infrastructure implementation is grouped under one package.
- [x] Compatibility shims preserve existing imports.

## Phase 8: CLI Package

Status: Done

Goal: Split CLI commands into focused modules without changing command names.

Tasks:

- [x] Create `voicekit/cli/__init__.py`.
- [x] Create `voicekit/cli/main.py`.
- [x] Create speech command module shell in `cli/commands/speech.py`.
- [x] Create transcription command module shell in `cli/commands/transcription.py`.
- [x] Create subtitle command module shell in `cli/commands/subtitles.py`.
- [x] Create translation command module shell in `cli/commands/translation.py`.
- [x] Create dubbing command module shell in `cli/commands/dubbing.py`.
- [x] Create diarization command module shell in `cli/commands/diarization.py`.
- [x] Create voice/profile command module shell in `cli/commands/voices.py`.
- [x] Keep CLI implementation compatible through `voicekit/cli_legacy.py`.

Validation:

- [x] `uv run python -m voicekit.cli --help`
- [x] `uv run python -m voicekit.cli emotion-script --help`
- [x] `uv run python -m voicekit.cli transcribe --help` remains covered by command registration.
- [x] `uv run python -m voicekit.cli subtitle-import --help` remains covered by command registration.
- [x] `uv run python -m voicekit.cli dub --help` remains covered by command registration.

Exit criteria:

- [x] CLI package shell is modular.
- [x] Existing commands and flags remain stable.

## Phase 9: MCP Package

Status: Done

Goal: Move MCP server code into a dedicated package.

Tasks:

- [x] Create `voicekit/mcp/__init__.py`.
- [x] Move MCP server setup into `mcp/server.py`.
- [x] Create `mcp/tools.py` shell.
- [x] Create `mcp/resources.py` shell.
- [x] Keep `voicekit/mcp_server.py` as a full compatibility module alias.

Validation:

- [x] Existing MCP unit tests pass through compatibility alias.
- [x] HTTP MCP server health endpoint is covered by existing tests.

Exit criteria:

- [x] MCP code is separate from API and core service modules.

## Phase 10: Legacy UI Isolation

Status: Done

Goal: Move Gradio legacy UI into a clearly marked legacy package.

Tasks:

- [x] Create `voicekit/legacy/__init__.py`.
- [x] Move `voicekit/ui.py` implementation into `legacy/ui.py`.
- [x] Keep `voicekit/ui.py` as a compatibility shim.
- [x] Verify `voicekit.ui:main` imports.

Validation:

- [x] `python -m py_compile voicekit/ui.py voicekit/legacy/ui.py`
- [x] `voicekit.ui:main` import smoke passes.

Exit criteria:

- [x] Legacy UI no longer sits beside active backend service modules.

## Phase 11: Import Migration

Status: Done

Goal: Move internal imports from compatibility shims to the new package paths.

Tasks:

- [x] Replace workflow-router imports of `voicekit.model_store` with `voicekit.infrastructure.model_store`.
- [x] Replace workflow-router imports of `voicekit.stores.*` with `voicekit.infrastructure.stores.*`.
- [x] Move database/media/model/stores implementations to infrastructure modules.
- [x] Add CLI package and command module shells.
- [x] Keep public shims for external compatibility.
- [ ] Optional follow-up: migrate every internal import in lower-level modules to infrastructure paths.

Validation:

- [x] Python compile across moved modules.
- [x] API, CLI, frontend build smoke pass.

Exit criteria:

- [x] New internal architecture contains the moved implementations and is used by app workflow router.
- [x] Compatibility shims preserve public/backward compatibility.

## Phase 12: Tests and Cleanup

Status: Done

Goal: Add focused regression coverage and remove only safe duplication.

Tasks:

- [x] Add app import/router registration smoke test.
- [x] Add compatibility entrypoint smoke test.
- [x] Existing transcription/translation/subtitle/model tests remain in test suite.
- [x] Existing Hugging Face token behavior remains covered by import/smoke and model-store implementation.
- [x] CLI command registration smoke passes.
- [x] Remove duplicate API app setup and schema definitions.
- [x] Update `docs/backend-structure-refactor-plan.md`.
- [x] No README entrypoint change required; `voicekit.api:app` remains stable.

Validation:

- [x] Relevant unit tests pass.
- [x] `python -m py_compile voicekit/api.py`
- [x] `uv run python -m voicekit.cli --help`
- [x] `cd frontend && pnpm build`

Exit criteria:

- [x] Refactor is documented and covered by smoke tests.
- [x] No user-facing behavior changed unexpectedly.

## Compatibility Shims to Keep During Migration

Keep these until all internal imports have moved and external compatibility has been considered:

- `voicekit/api.py`
- `voicekit/cli.py`
- `voicekit/model_store.py`
- `voicekit/database.py`
- `voicekit/media.py`
- `voicekit/ui.py`
- `voicekit/mcp_server.py`
- `voicekit/stores/*`

## High-Risk Flows to Recheck After Every Major Phase

- Speech generation:
  - `/v1/audio/speech`
  - `/v1/audio/speech/clone`
  - `/v1/audio/speech/design`
  - `/v1/audio/speech/emotion-script`
- Transcription:
  - `/v1/audio/transcriptions`
  - `translate=true`
  - `response_format=srt`
  - `response_format=vtt`
  - queued transcription
- Subtitle tools:
  - `/v1/subtitles/import`
  - `/v1/subtitles/export`
- Translation:
  - `/v1/translation/providers`
  - `/v1/translation/translate`
  - model-provider translation
- Dubbing:
  - `/v1/dubbing/dub-upload`
  - diarization toggle
  - speaker voice map
- Settings:
  - Hugging Face token save/load
  - provider model CRUD
  - provider model model-list execution
- Jobs:
  - list
  - cancel
  - delete
  - download artifacts

## Current Decision Log

- Approved target structure: accepted by project owner.
- Refactor must be sequential by phase.
- `voicekit.api:app` remains the public backend entrypoint until explicitly changed.
- Frontend API contracts must remain stable.
- Hugging Face token from Settings should be used for all model downloads through the model store.
