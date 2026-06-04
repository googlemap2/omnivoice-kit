# OmniVoice Desktop

Tauri desktop client for the OmniVoice backend server.

## Scope

- Desktop app is a client only.
- Backend/model runtime stays on a separate FastAPI server.
- Backend URL is configured at runtime in the app and saved locally.

## Development

Prerequisites:

- Node.js and pnpm.
- Rust toolchain.
- Tauri system dependencies for your OS.

Install dependencies:

```bash
cd desktop
pnpm install
```

Run web UI only:

```bash
pnpm dev
```

Run Tauri desktop app:

```bash
pnpm desktop:dev
```

Build frontend:

```bash
pnpm build
```

Build desktop bundle:

```bash
pnpm desktop:build
```

## Backend Connection

Start the backend server separately, then set the URL in the desktop app:

```bash
cd backend
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Examples:

- `http://127.0.0.1:8000`
- `https://your-backend.ngrok-free.dev`

The app tests connectivity with `/health` and sends the `ngrok-skip-browser-warning` header.
