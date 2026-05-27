# OmniVoice Kit Frontend

Next.js studio UI for the local FastAPI backend.

## Setup

```bash
pnpm install
cp .env.local.example .env.local
```

## Run

Terminal 1, from the repository root:

```bash
uv run uvicorn voicekit.api:app --host 127.0.0.1 --port 8000
```

Terminal 2, from `frontend/`:

```bash
pnpm dev
```

Open `http://localhost:3000`.

## Configuration

Set the backend URL in `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The UI uses a VS Code-style studio layout with MUI: activity bar, explorer sidebar, editor workspace, and bottom output panel.

## Source Structure

```text
src/
  app/                  Next.js App Router entrypoints, route group, and providers
    (studio)/           Shared studio shell layout
      speech/           /speech
      transcription/    /transcription
      translation/      /translation
      voices/           /voices
      settings/         /settings
  components/
    layout/             Studio shell pieces: title bar, activity bar, explorer, bottom panel
    ui/                 Reusable MUI form controls
  features/
    settings/           Settings workspace
    speech/             TTS and voice clone workspace
    studio/             Shared studio provider/frame and API orchestration
    transcription/      ASR workspace
    translation/        Translation workspace
    voices/             Voice profile workspace
  lib/                  API client helpers
  types/                Shared API and studio types
```
