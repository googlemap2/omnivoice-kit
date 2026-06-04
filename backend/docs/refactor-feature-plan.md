# OmniVoice Kit Refactor and Feature Plan

Use this file to track refactor and feature work. Check each task after it is completed.

## Phase 1: Extract Backend Core

- [x] Create shared backend core module `backend/core.py`.
- [x] Move model, language, and instruct constants out of the Gradio UI.
- [x] Move device/dtype selection out of the Gradio UI.
- [x] Move model loading and model cache logic out of the Gradio UI.
- [x] Move voice clone prompt loading for `.pt` and `.npy`.
- [x] Move `speakers.json` read/write logic.
- [x] Move speaker choice listing logic.
- [x] Move speaker id creation logic.
- [x] Move speaker id rename logic.
- [x] Move speaker id delete logic.
- [x] Move `generate_clone_with_speaker_id`.
- [x] Move `generate_clone_with_ref_audio`.
- [x] Move `generate_voice_design`.
- [x] Update Gradio UI to import and call backend core instead of holding business logic.
- [x] Run syntax checks for changed files.
- [x] Run smoke import for the core module without loading the real model.

## Phase 2: Refactor CLI to Use Core

- [x] Update CLI implementation to use backend core.
- [x] Remove duplicated `VALID_INSTRUCTS_EN/ZH` from CLI.
- [x] Remove duplicated `pick_device` from CLI if core owns it.
- [x] Remove duplicated `load_voice_clone_prompt` from CLI if core owns it.
- [x] Verify `speaker-id` command still works.
- [x] Verify `ref-audio` command still works.
- [x] Verify `voice-design` command still works.
- [x] Update README if command usage or behavior changes.

## Phase 3: Voice Profiles v1

- [x] Create `VoiceProfileStore` abstraction.
- [x] Keep backward compatibility with `speakers.json`.
- [x] Standardize profile fields: `id`, `name`, `type`, `prompt_path`, `language`.
- [x] Add metadata fields: `ref_text`, `created_at`, `updated_at`.
- [x] Add `list_profiles()`.
- [x] Add `get_profile(id)`.
- [x] Add `create_profile(...)`.
- [x] Add `rename_profile(...)`.
- [x] Add `delete_profile(...)`.
- [x] Update UI speaker dropdown to use profile store.
- [x] Update CLI speaker-id mode to use profile store.

## Phase 4: OpenAI-Compatible Speech API

- [x] Add FastAPI/uvicorn dependencies if missing.
- [x] Create a separate FastAPI app in `backend/api.py`.
- [x] Add `/health`.
- [x] Add `/v1/models`.
- [x] Add `/v1/voices`.
- [x] Add `/v1/audio/speech`.
- [x] Map OpenAI-style requests into backend core generation requests.
- [x] Return WAV or another initially supported audio format.
- [x] Add README section for running the API server.
- [x] Smoke test `/health`.

## Phase 5: Basic Model Status and Install UI

- [x] Extract model status helpers from `model_store.py`.
- [x] Report model status: installed or missing.
- [x] Check `config.json`.
- [x] Check weight files.
- [x] Show local model path.
- [x] Add model status to UI or API.
- [x] Add install/download action for missing model.
- [x] Add minimal progress/log output for download.

## Backend Structure Cleanup

- [x] Create `backend/` backend package.
- [x] Move backend core implementation to `backend/core.py`.
- [x] Move voice profile implementation to `backend/profiles.py`.
- [x] Move model store implementation to `backend/model_store.py`.
- [x] Move FastAPI implementation to `backend/api.py`.
- [x] Remove root compatibility shims after moving internal imports to `backend.*`.
- [x] Update UI and CLI implementation imports to use `backend.*`.
- [x] Update package metadata to install `backend`.
- [x] Verify `uv sync` builds the package.

## Phase 6: Generation History

- [x] Choose initial storage: PostgreSQL.
- [x] Save metadata for each generation.
- [x] Save mode: `speaker-id`, `ref-audio`, `voice-design`.
- [x] Save model id/source.
- [x] Save generation params.
- [x] Save output path.
- [x] Add history listing helper/API.
- [x] Add basic history UI.

## Phase 7: Audio DSP Presets

- [x] Split raw generation and audio post-processing into separate steps.
- [x] Add preset `raw`.
- [x] Add preset `normalize`.
- [x] Add preset `broadcast`.
- [x] Add effect preset option to UI.
- [x] Add effect preset option to CLI/API.

## Phase 8: Settings

- [x] Add local settings storage.
- [x] Save default model.
- [x] Save default device.
- [x] Save default effect preset.
- [x] Save output directory.
- [x] Add settings API.
- [x] Add basic settings UI.
- [x] Use settings defaults in CLI and UI.

## Phase 9: ASR Transcription

- [x] Add ASR backend module.
- [x] Use `faster-whisper` as the first ASR backend.
- [x] Support audio/video file transcription through ffmpeg-backed decoding.
- [x] Return full text and timestamped segments.
- [x] Support output formats: JSON, plain text, verbose JSON, SRT, VTT.
- [x] Add ASR CLI command.
- [x] Add basic ASR UI.

## Phase 10: OpenAI-Compatible Transcription Endpoint

- [x] Add `/v1/audio/transcriptions`.
- [x] Accept multipart file upload.
- [x] Accept OpenAI-style fields: `model`, `language`, `response_format`.
- [x] Return text, JSON, verbose JSON, SRT, or VTT.

## Feature Phase Status

Use this overview to see which feature group is done, in progress, or still pending.

| Feature | Related phases | Status |
|---|---:|---|
| Backend core extraction | Phase 1 | Done |
| CLI core integration | Phase 2 | Mostly done |
| Voice profiles v1 | Phase 3 | Done |
| Speech API | Phase 4 | Done |
| Model status/install | Phase 5 | Done |
| Generation history | Phase 6 | Done |
| Audio DSP presets | Phase 7 | Done |
| Settings | Phase 8 | Done |
| ASR transcription | Phase 9 | Done |
| OpenAI transcription API | Phase 10 | Done |
| Translation provider registry | Phase 11 | Done |
| Subtitle import/export | Phase 12 | Done |
| Video dubbing | Phase 13 | Done |
| Speaker diarization | Phase 14 | Done |
| Realtime dictation | Phase 15 | Mostly done |
| Batch queue | Phase 16 | Mostly done |
| Voice gallery | Phase 17 | Done |
| Logs and diagnostics | Phase 19 | Done |
| MCP server | Phase 20 | Done |
| Marketplace/import/export | Phase 21 | Done |
| Desktop packaging | Phase 22 | Pending |

## Phase 11: Translation Provider Registry

Related feature: Translation.

- [x] Create `backend/translation.py`.
- [x] Define provider interface: `list_languages()`, `translate_text()`, `translate_segments()`.
- [x] Add offline stub provider for no-op/source text passthrough.
- [x] Add NLLB provider adapter if local NLLB code is kept in this repo.
- [x] Add optional online provider config placeholders: Google, DeepL, Microsoft, MyMemory.
- [x] Store provider settings/API keys through settings layer.
- [x] Add `/v1/translation/providers`.
- [x] Add `/v1/translation/translate`.
- [x] Add CLI command `backend translate`.
- [x] Add basic Translation tab in UI.
- [x] Add smoke tests with no-op provider.
- [x] Update README.

## Phase 12: Subtitle Import, Edit, and Export

Related feature: Subtitle import/export.

- [x] Create `backend/subtitles.py`.
- [x] Define subtitle segment dataclass: `id`, `start`, `end`, `text`, `speaker`, `metadata`.
- [x] Parse `.srt`.
- [x] Parse `.vtt`.
- [x] Validate timestamps and sort cues.
- [x] Export `.srt`.
- [x] Export `.vtt`.
- [x] Convert ASR transcription result into subtitle segments.
- [x] Add subtitle import/export API endpoints.
- [x] Add CLI commands: `subtitle-import`, `subtitle-export`, `transcribe --format srt/vtt`.
- [x] Add basic subtitle preview/editor UI.
- [x] Add unit tests for SRT/VTT roundtrip.
- [x] Update README.

## Phase 13: Video Dubbing Pipeline v1

Related feature: Video dubbing.

- [x] Create `backend/media.py` for ffmpeg wrappers.
- [x] Add ffmpeg availability check.
- [x] Extract audio from video/audio input.
- [x] Run ASR to timestamped segments.
- [x] Translate segments through translation registry.
- [x] Assign one voice profile to all segments for v1.
- [x] Generate TTS per segment.
- [x] Fit generated audio to segment timing with simple padding/trimming.
- [x] Mix dubbed speech track.
- [x] Export dubbed WAV.
- [x] Export SRT/VTT subtitles.
- [x] Export dubbed video with original video stream.
- [x] Add API endpoint to start dubbing job.
- [x] Add CLI command `backend dub`.
- [x] Add basic Dubbing tab in UI.
- [x] Add smoke test with short audio fixture and mocked ASR/translation/TTS backends.
- [x] Update README.

## Phase 14: Speaker Diarization

Related feature: Speaker diarization.

- [x] Create `backend/diarization.py`.
- [x] Add optional pyannote dependency strategy.
- [x] Add Hugging Face token setting.
- [x] Add pyannote license/token error messages.
- [x] Run diarization on source audio.
- [x] Merge diarization speaker labels into ASR subtitle segments.
- [x] Add speaker-to-voice assignment structure.
- [x] Add API endpoint for diarization.
- [x] Add CLI command `backend diarize`.
- [x] Add diarization controls to Dubbing UI.
- [x] Add smoke tests with mocked diarization backend.
- [x] Update README.

## Phase 15: Realtime Dictation

Related feature: Realtime dictation.

- [x] Create streaming ASR abstraction.
- [x] Add WebSocket endpoint for audio chunks.
- [x] Add partial/final transcript event schema.
- [ ] Add silence/end-of-utterance detection.
- [x] Add microphone capture UI prototype in frontend if feasible.
- [ ] Add CLI microphone dictation prototype if feasible.
- [x] Add settings for dictation model/device/language.
- [x] Add smoke tests for WebSocket protocol with fake ASR backend.
- [x] Update README.

## Phase 16: Batch Queue

Related feature: Batch queue.

- [x] Create `backend/jobs.py`.
- [x] Add PostgreSQL job table.
- [x] Define job states: pending, running, completed, failed, canceled.
- [x] Add worker loop for TTS/ASR/translation/dubbing jobs.
- [x] Persist job params and result paths.
- [x] Add cancel/delete job operations.
- [x] Add `/v1/jobs` list/create/detail/cancel endpoints.
- [x] Add basic queue UI.
- [x] Route long-running TTS/ASR/translation/dubbing through job queue.
- [x] Add smoke tests for job lifecycle.
- [x] Update README.

## Phase 17: Voice Gallery

Related feature: Voice gallery.

- [x] Extend profile metadata with tags, favorite flag, notes, preview path.
- [x] Add filesystem storage convention for voice assets.
- [x] Add profile search/filter helpers.
- [x] Add voice preview generation.
- [x] Add profile import from local audio.
- [x] Add profile export metadata.
- [x] Add `/v1/voice-profiles` CRUD endpoints.
- [x] Add gallery UI with search/favorite/delete.
- [x] Add tests for profile metadata migration.
- [x] Update README.

## Phase 19: Logs and Diagnostics

Related feature: Settings and diagnostics.

- [x] Add Python logging config with rotating file handler.
- [x] Add log redaction for tokens/API keys.
- [x] Add system info helper: OS, Python, device, CUDA/MPS status.
- [x] Add ffmpeg availability diagnostic.
- [x] Add model cache diagnostic.
- [x] Add `/v1/diagnostics`.
- [x] Add `/v1/logs`.
- [x] Add UI Diagnostics tab.
- [x] Add clear logs action.
- [x] Add smoke tests for redaction and diagnostics.
- [x] Update README.

## Phase 20: MCP Server

Related feature: MCP server.

- [x] Decide MCP transport: stdio first, HTTP later.
- [x] Add HTTP JSON-RPC transport.
- [x] Create `backend/mcp_server.py`.
- [x] Expose tool: generate speech.
- [x] Expose tool: transcribe audio.
- [x] Expose tool: list voices.
- [x] Expose tool: list languages.
- [x] Expose resource: recent generation history.
- [x] Add console script `backend-mcp`.
- [x] Add smoke tests for tool registration.
- [x] Update README with MCP config example.

## Phase 21: Marketplace and Import/Export

Related feature: Marketplace/import/export.

- [x] Define voice package format.
- [x] Export voice profile package as `.zip`.
- [x] Include metadata JSON.
- [x] Include reference/preview audio if available.
- [x] Validate package on import.
- [x] Import package as voice profile.
- [x] Add local package directory.
- [x] Add API endpoints for import/export.
- [x] Add UI import/export actions.
- [x] Add tests for package roundtrip.
- [x] Update README.

## Phase 22: Desktop Packaging

Related feature: Desktop packaging with Tauri/React.

- [ ] Decide desktop app structure: keep Gradio or add React/Tauri.
- [ ] If using React/Tauri, create frontend workspace.
- [ ] Add API process startup strategy.
- [ ] Add local app settings path strategy for packaged app.
- [ ] Add model/data path strategy for packaged app.
- [ ] Add Windows packaging target.
- [ ] Add macOS packaging target.
- [ ] Add Linux packaging target.
- [ ] Add installer smoke checklist.
- [ ] Update README with desktop build instructions.

## Done Log

- [x] Created initial refactor and feature tracking plan.
- [x] Completed Phase 1 backend core extraction: `backend/core.py` owns generation, model, prompt, and speaker registry logic; `backend/ui.py` now only builds the Gradio UI.
- [x] Refactored CLI to use `backend/core.py` for model loading, instruct parsing, speaker registry loading, and prompt loading. CLI help was smoke tested for all subcommands.
- [x] Verified all three CLI inference modes: `speaker-id`, `ref-audio`, and `voice-design`.
- [x] Completed Voice Profiles v1 with `VoiceProfileStore`, legacy `speakers.json` compatibility, normalized profile metadata, and UI/CLI integration.
- [x] Added FastAPI speech API with `/health`, `/v1/models`, `/v1/voices`, `/v1/languages`, and `/v1/audio/speech`; smoke tested non-generating endpoints and missing-voice error path.
- [x] Verified `/v1/audio/speech` real generation path and wrote `api_speech.wav`.
- [x] Reorganized backend code into `backend/` package and removed unnecessary root shims.
- [x] Moved UI, CLI, and helper scripts from legacy `omnivoice/` folder into `backend/`, then removed the legacy folder.
- [x] Completed Phase 5 basic model status/install support in `backend.model_store`, FastAPI, and Gradio UI.
- [x] Completed Phase 6 PostgreSQL generation history with core/CLI recording, API listing, and Gradio History tab.
- [x] Completed Phase 7 audio DSP presets with raw/normalize/broadcast options in core, UI, CLI, and API.
- [x] Completed Phase 8 local settings with JSON storage, API endpoints, UI tab, and CLI/UI defaults.
- [x] Completed Phase 9 ASR transcription with lazy `faster-whisper` backend, CLI command, and Gradio Transcription tab.
- [x] Completed Phase 10 OpenAI-compatible transcription endpoint at `/v1/audio/transcriptions`.
- [x] Completed Phase 11 translation provider registry with `backend/translation.py`, passthrough/NLLB/online placeholders, settings fields, API/CLI/UI, and unittest smoke tests.
- [x] Completed Phase 12 subtitle import/export with SRT/VTT parsing, JSON segment conversion, API/CLI hooks, Transcription UI import/export plus integrated ASR+translate options and raw/translated subtitle downloads, and roundtrip tests.
- [x] Completed Phase 13 video dubbing v1 with ffmpeg media helpers, synchronous ASR/translation/TTS pipeline, dubbed WAV/SRT/VTT/video outputs, API/CLI hooks, Dubbing UI, timing unit tests, and a short-audio smoke test with mocked heavy backends.
- [x] Completed Phase 14 speaker diarization v1 with optional pyannote backend, Hugging Face token setting/env fallback, diarization API/CLI, speaker-label merge helpers, speaker-to-voice assignment structure, Dubbing UI toggle, and mocked merge tests.
- [x] Implemented Phase 15 realtime dictation v1 with WebSocket audio chunks, ready/partial/final/done/error events, browser microphone capture in Transcription, fake protocol test helpers, and README notes. Silence detection and CLI microphone mode remain pending.
- [x] Implemented Phase 16 batch queue v1 with Supabase/PostgreSQL jobs, background worker, job lifecycle API, queued Speech/Transcription/Translation/Dubbing modes, Jobs UI, and lifecycle tests. Fine-grained progress/cancel for already-running inference remains pending.
- [x] Completed Phase 17 voice gallery with backward-compatible profile metadata migration, asset directory convention, profile search/filter helpers, `/v1/voice-profiles` CRUD endpoints, local-audio import, preview generation, metadata export, gallery search/favorite/delete UI, and metadata migration tests.
- [x] Completed Phase 19 logs and diagnostics with rotating redacted logs, system/device/ffmpeg/model-cache diagnostics, `/v1/diagnostics`, `/v1/logs`, clear logs, Settings Diagnostics UI, and smoke tests.
- [x] Implemented Phase 20 MCP stdio/HTTP server v1 with list/generate/transcribe tools, recent history resource, console script, README config, and handler/HTTP smoke tests.
- [x] Completed Phase 21 voice package import/export with `.voicepkg.zip` manifest/assets, API endpoints, Voice Gallery UI import/export actions, local package export directory, and roundtrip tests.
