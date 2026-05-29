# OmniVoice Kit Refactor and Feature Plan

Use this file to track refactor and feature work. Check each task after it is completed.

## Phase 1: Extract Backend Core

- [x] Create shared backend core module `voicekit/core.py`.
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
- [x] Create a separate FastAPI app in `voicekit/api.py`.
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

- [x] Create `voicekit/` backend package.
- [x] Move backend core implementation to `voicekit/core.py`.
- [x] Move voice profile implementation to `voicekit/profiles.py`.
- [x] Move model store implementation to `voicekit/model_store.py`.
- [x] Move FastAPI implementation to `voicekit/api.py`.
- [x] Remove root compatibility shims after moving internal imports to `voicekit.*`.
- [x] Update UI and CLI implementation imports to use `voicekit.*`.
- [x] Update package metadata to install `voicekit`.
- [x] Verify `uv sync` builds the package.

## Phase 6: Generation History

- [x] Choose initial storage: SQLite or JSONL.
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
| Video dubbing | Phase 13 | Pending |
| Speaker diarization | Phase 14 | Pending |
| Realtime dictation | Phase 15 | Pending |
| Batch queue | Phase 16 | Pending |
| Voice gallery | Phase 17 | Pending |
| Watermarking | Phase 18 | Pending |
| Logs and diagnostics | Phase 19 | Pending |
| MCP server | Phase 20 | Pending |
| Marketplace/import/export | Phase 21 | Pending |
| Desktop packaging | Phase 22 | Pending |

## Phase 11: Translation Provider Registry

Related feature: Translation.

- [x] Create `voicekit/translation.py`.
- [x] Define provider interface: `list_languages()`, `translate_text()`, `translate_segments()`.
- [x] Add offline stub provider for no-op/source text passthrough.
- [x] Add NLLB provider adapter if local NLLB code is kept in this repo.
- [x] Add optional online provider config placeholders: Google, DeepL, Microsoft, MyMemory.
- [x] Store provider settings/API keys through settings layer.
- [x] Add `/v1/translation/providers`.
- [x] Add `/v1/translation/translate`.
- [x] Add CLI command `voicekit translate`.
- [x] Add basic Translation tab in UI.
- [x] Add smoke tests with no-op provider.
- [x] Update README.

## Phase 12: Subtitle Import, Edit, and Export

Related feature: Subtitle import/export.

- [x] Create `voicekit/subtitles.py`.
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

- [ ] Create `voicekit/media.py` for ffmpeg wrappers.
- [ ] Add ffmpeg availability check.
- [ ] Extract audio from video/audio input.
- [ ] Run ASR to timestamped segments.
- [ ] Translate segments through translation registry.
- [ ] Assign one voice profile to all segments for v1.
- [ ] Generate TTS per segment.
- [ ] Fit generated audio to segment timing with simple padding/trimming.
- [ ] Mix dubbed speech track.
- [ ] Export dubbed WAV.
- [ ] Export SRT/VTT subtitles.
- [ ] Export dubbed video with original video stream.
- [ ] Add API endpoint to start dubbing job.
- [ ] Add CLI command `voicekit dub`.
- [ ] Add basic Dubbing tab in UI.
- [ ] Add smoke test with short audio/video fixture.
- [ ] Update README.

## Phase 14: Speaker Diarization

Related feature: Speaker diarization.

- [ ] Create `voicekit/diarization.py`.
- [ ] Add optional pyannote dependency strategy.
- [ ] Add Hugging Face token setting.
- [ ] Add pyannote license/token error messages.
- [ ] Run diarization on source audio.
- [ ] Merge diarization speaker labels into ASR subtitle segments.
- [ ] Add speaker-to-voice assignment structure.
- [ ] Add API endpoint for diarization.
- [ ] Add CLI command `voicekit diarize`.
- [ ] Add diarization controls to Dubbing UI.
- [ ] Add smoke tests with mocked diarization backend.
- [ ] Update README.

## Phase 15: Realtime Dictation

Related feature: Realtime dictation.

- [ ] Create streaming ASR abstraction.
- [ ] Add WebSocket endpoint for audio chunks.
- [ ] Add partial/final transcript event schema.
- [ ] Add silence/end-of-utterance detection.
- [ ] Add microphone capture UI prototype in Gradio if feasible.
- [ ] Add CLI microphone dictation prototype if feasible.
- [ ] Add settings for dictation model/device/language.
- [ ] Add smoke tests for WebSocket protocol with fake ASR backend.
- [ ] Update README.

## Phase 16: Batch Queue

Related feature: Batch queue.

- [ ] Create `voicekit/jobs.py`.
- [ ] Add SQLite job table.
- [ ] Define job states: pending, running, completed, failed, canceled.
- [ ] Add worker loop for TTS/ASR/translation/dubbing jobs.
- [ ] Persist job params and result paths.
- [ ] Add cancel/delete job operations.
- [ ] Add `/v1/jobs` list/create/detail/cancel endpoints.
- [ ] Add basic queue UI.
- [ ] Route long-running dubbing through job queue.
- [ ] Add smoke tests for job lifecycle.
- [ ] Update README.

## Phase 17: Voice Gallery

Related feature: Voice gallery.

- [ ] Extend profile metadata with tags, favorite flag, notes, preview path.
- [ ] Add filesystem storage convention for voice assets.
- [ ] Add profile search/filter helpers.
- [ ] Add voice preview generation.
- [ ] Add profile import from local audio.
- [ ] Add profile export metadata.
- [ ] Add `/v1/voice-profiles` CRUD endpoints.
- [ ] Add gallery UI with search/favorite/delete.
- [ ] Add tests for profile metadata migration.
- [ ] Update README.

## Phase 18: Watermarking

Related feature: Watermarking.

- [ ] Choose watermark backend or define placeholder interface.
- [ ] Add optional watermark settings.
- [ ] Embed watermark after TTS generation.
- [ ] Detect watermark from uploaded audio.
- [ ] Record watermark metadata in generation history.
- [ ] Add API endpoint for watermark detection.
- [ ] Add UI controls for watermark on/off and detection.
- [ ] Add tests with mocked watermark backend.
- [ ] Update README.

## Phase 19: Logs and Diagnostics

Related feature: Settings and diagnostics.

- [ ] Add Python logging config with rotating file handler.
- [ ] Add log redaction for tokens/API keys.
- [ ] Add system info helper: OS, Python, device, CUDA/MPS status.
- [ ] Add ffmpeg availability diagnostic.
- [ ] Add model cache diagnostic.
- [ ] Add `/v1/diagnostics`.
- [ ] Add `/v1/logs`.
- [ ] Add UI Diagnostics tab.
- [ ] Add clear logs action.
- [ ] Add smoke tests for redaction and diagnostics.
- [ ] Update README.

## Phase 20: MCP Server

Related feature: MCP server.

- [ ] Decide MCP transport: stdio first, HTTP later.
- [ ] Create `voicekit/mcp_server.py`.
- [ ] Expose tool: generate speech.
- [ ] Expose tool: transcribe audio.
- [ ] Expose tool: list voices.
- [ ] Expose tool: list languages.
- [ ] Expose resource: recent generation history.
- [ ] Add console script `voicekit-mcp`.
- [ ] Add smoke tests for tool registration.
- [ ] Update README with MCP config example.

## Phase 21: Marketplace and Import/Export

Related feature: Marketplace/import/export.

- [ ] Define voice package format.
- [ ] Export voice profile package as `.zip`.
- [ ] Include metadata JSON.
- [ ] Include reference/preview audio if available.
- [ ] Validate package on import.
- [ ] Import package as voice profile.
- [ ] Add local package directory.
- [ ] Add API endpoints for import/export.
- [ ] Add UI import/export actions.
- [ ] Add tests for package roundtrip.
- [ ] Update README.

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
- [x] Completed Phase 1 backend core extraction: `voicekit/core.py` owns generation, model, prompt, and speaker registry logic; `voicekit/ui.py` now only builds the Gradio UI.
- [x] Refactored CLI to use `voicekit/core.py` for model loading, instruct parsing, speaker registry loading, and prompt loading. CLI help was smoke tested for all subcommands.
- [x] Verified all three CLI inference modes: `speaker-id`, `ref-audio`, and `voice-design`.
- [x] Completed Voice Profiles v1 with `VoiceProfileStore`, legacy `speakers.json` compatibility, normalized profile metadata, and UI/CLI integration.
- [x] Added FastAPI speech API with `/health`, `/v1/models`, `/v1/voices`, `/v1/languages`, and `/v1/audio/speech`; smoke tested non-generating endpoints and missing-voice error path.
- [x] Verified `/v1/audio/speech` real generation path and wrote `api_speech.wav`.
- [x] Reorganized backend code into `voicekit/` package and removed unnecessary root shims.
- [x] Moved UI, CLI, and helper scripts from legacy `omnivoice/` folder into `voicekit/`, then removed the legacy folder.
- [x] Completed Phase 5 basic model status/install support in `voicekit.model_store`, FastAPI, and Gradio UI.
- [x] Completed Phase 6 SQLite generation history with core/CLI recording, API listing, and Gradio History tab.
- [x] Completed Phase 7 audio DSP presets with raw/normalize/broadcast options in core, UI, CLI, and API.
- [x] Completed Phase 8 local settings with JSON storage, API endpoints, UI tab, and CLI/UI defaults.
- [x] Completed Phase 9 ASR transcription with lazy `faster-whisper` backend, CLI command, and Gradio Transcription tab.
- [x] Completed Phase 10 OpenAI-compatible transcription endpoint at `/v1/audio/transcriptions`.
- [x] Completed Phase 11 translation provider registry with `voicekit/translation.py`, passthrough/NLLB/online placeholders, settings fields, API/CLI/UI, and unittest smoke tests.
- [x] Completed Phase 12 subtitle import/export with SRT/VTT parsing, JSON segment conversion, API/CLI hooks, basic Transcription UI import/export, and roundtrip tests.
