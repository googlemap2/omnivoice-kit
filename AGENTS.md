# AGENTS.md

Guidance for agents and developers working in the `omnivoice-kit` repository.

## Execution Principles

- Think before coding:
  - State assumptions explicitly before implementation.
  - If multiple interpretations exist, present options instead of silently picking one.
  - If a simpler approach exists, prefer it and call out tradeoffs.
  - If requirements are unclear, stop and ask for clarification.
- Simplicity first:
  - Implement the minimum code needed for the requested outcome.
  - Do not add speculative features, unused abstractions, or unnecessary configurability.
  - Avoid extra error handling for impossible scenarios.
  - If a solution is overcomplicated, simplify it before finalizing.
- Surgical changes:
  - Touch only files/lines required by the task.
  - Do not refactor or reformat unrelated code.
  - Match existing style and patterns in the touched area.
  - Remove only unused code introduced by your own changes.
  - If unrelated dead code is discovered, report it separately instead of deleting it.
- Goal-driven execution:
  - Convert requests into verifiable success criteria.
  - For bug fixes, prefer a failing reproduction check first, then verify it passes.
  - For behavior changes/refactors, verify expected behavior before and after change.
  - For multi-step tasks, keep a short step list with a validation check per step.

## Read First

1. Read [docs/project-handoff-vi.md](docs/project-handoff-vi.md) to understand the product goals, tech stack, models, FE/API/CLI flows, and feature status.
2. Read [README.md](README.md) for installation, backend/frontend startup, and main CLI commands.
3. Read [docs/refactor-feature-plan.md](docs/refactor-feature-plan.md) if you need phase status or pending work.
4. For a specific backend feature, read the endpoint in `voicekit/api.py` first, then inspect the corresponding module.
5. For frontend work, read `frontend/src/components/studio/StudioContext.tsx` before the page file because it owns state and API actions.

## Project Overview

`omnivoice-kit` is a local-first AI voice studio:

- OmniVoice TTS.
- Zero-shot voice cloning from reference audio.
- Voice design with instruct items.
- Voice profiles through `speaker_id`.
- Emotion-script TTS with per-segment tags.
- ASR transcription with `faster-whisper`.
- SRT/VTT subtitle import/export.
- Translation provider registry.
- Audio/video dubbing.
- Speaker diarization with `pyannote.audio` when dependencies and tokens are available.
- Realtime dictation over WebSocket.
- Batch queue/jobs.
- OpenAI-compatible speech/transcription APIs.

## Tech Stack

Backend:

- Python package in `voicekit/`.
- FastAPI app in `voicekit/api.py`.
- CLI in `voicekit/cli.py`.
- Model runtime: OmniVoice/PyTorch.
- ASR: `faster-whisper`.
- Audio/video: `soundfile`, `numpy`, FFmpeg helpers.
- Local settings: `data/settings.json`.
- Local model cache: `models/`.
- Jobs/history: PostgreSQL/Supabase when `VOICEKIT_DATABASE_URL` is configured.

Frontend:

- Next.js 15 App Router, React 19.
- MUI 6.
- API client in `frontend/src/lib/api.ts`.
- Studio state in `frontend/src/components/studio/StudioContext.tsx`.
- Main pages in `frontend/src/app/(studio)/`.

## Key Backend Modules

- `voicekit/core.py`: model loading, device/dtype selection, prompts, speaker-id/ref-audio/voice-design TTS.
- `voicekit/emotion_tts.py`: emotion tag parsing, per-segment rendering, audio concatenation.
- `voicekit/api.py`: FastAPI endpoints.
- `voicekit/cli.py`: CLI subcommands.
- `voicekit/profiles.py`: `VoiceProfileStore` and `speakers.json` compatibility.
- `voicekit/model_store.py`: model status/install/cache.
- `voicekit/asr.py`: transcription.
- `voicekit/subtitles.py`: SRT/VTT import/export.
- `voicekit/translation.py`: translation providers.
- `voicekit/dubbing.py`: dubbing pipeline.
- `voicekit/diarization.py`: pyannote diarization.
- `voicekit/dictation.py`: realtime dictation helpers.
- `voicekit/jobs.py`: queue worker/store.
- `voicekit/settings.py`: app settings.

## Frontend Value/Label Contract

Important: localized UI labels are display-only. Backend-facing values must remain stable technical IDs.

- Instruct dropdown:
  - Display: `instructLabel(item)`.
  - Value: `item`.
  - Backend receives `instruct_items: string[]`.
- Emotion tag picker:
  - Display: localized labels such as `Thì thầm`, `Hào hứng`, `Suy tư`.
  - Inserted script value: `[whisper]`, `[excited]`, `[thoughtful]`.
  - Backend parses those values through `DEFAULT_TAG_ALIASES` in `voicekit/emotion_tts.py`.
- Voice dropdown:
  - Display: `voice.name || voice.id`.
  - Value: `voice.id`.

Do not change an `id` or backend value just to change UI copy. If a value must change, update backend mapping and test FE/API/CLI together.

## Current Emotion Script Flow

Frontend:

- Page: `frontend/src/app/(studio)/speech/page.tsx`.
- Mode: `emotion`.
- User types `@` to open the localized emotion tag picker.
- Clicking a tag inserts `[tag]` into the script.
- `StudioContext.generateSpeech()` calls `POST /v1/audio/speech/emotion-script`.

Backend:

- Endpoint: `create_emotion_script_speech()` in `voicekit/api.py`.
- Renderer: `render_emotion_tts_speaker_id()` in `voicekit/emotion_tts.py`.
- Default tag mapping:
  - `whisper` -> `whisper`
  - `excited` -> `high pitch`
  - `surprised` -> `very high pitch`
  - `thoughtful` -> `moderate pitch`
  - `laughing` -> `high pitch`
  - `chuckles` -> `high pitch`

This is v1: tags are mapped to OmniVoice instruct strings; this is not native model-level emotion control.

## Running The Project

Backend:

```bash
uv run uvicorn voicekit.api:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
pnpm dev
```

Frontend env:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

When using an ngrok/Colab backend, set `NEXT_PUBLIC_API_BASE_URL` to the backend ngrok URL. The backend must include the latest code and be restarted after new endpoints are added.

## Verification After Changes

Backend syntax:

```bash
python -m py_compile voicekit/api.py voicekit/emotion_tts.py
```

CLI smoke:

```bash
uv run python -m voicekit.cli --help
uv run python -m voicekit.cli emotion-script --help
```

Frontend build:

```bash
cd frontend
pnpm build
```

If `pnpm build` fails with `.next` ENOENT after a dev server was running, stop the dev server and remove the build artifact:

```powershell
Remove-Item -LiteralPath .next -Recurse -Force
pnpm build
```

## Editing Rules

- Keep changes small and scoped to the feature module.
- Do not change API contracts unless required.
- Do not turn display labels into backend values.
- Do not commit generated models, cache files, output media, or generated audio.
- Do not delete `models/`, `data/`, or `outputs/` unless the user explicitly asks.
- Do not revert user changes.
- Whenever adding or updating a feature, update the relevant documentation in `docs/` in the same change.
- For frontend changes, follow the existing MUI/context patterns.
- For backend changes, prefer existing helpers in `voicekit/*` before adding new abstractions.

## Related Docs

- [docs/project-handoff-vi.md](docs/project-handoff-vi.md): full handoff document.
- [docs/omnivoice-kit-feature-notes.md](docs/omnivoice-kit-feature-notes.md): product feature spec and vision.
- [docs/refactor-feature-plan.md](docs/refactor-feature-plan.md): roadmap and phase status.
- [frontend/README.md](frontend/README.md): frontend setup and configuration.
