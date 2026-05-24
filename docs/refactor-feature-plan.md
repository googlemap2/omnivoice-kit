# OmniVoice Kit Refactor and Feature Plan

Use this file to track refactor and feature work. Check each task after it is completed.

## Phase 1: Extract Backend Core

- [x] Create a shared backend core module, for example `omnivoice_core.py` or `voicekit_core.py`.
- [x] Move model, language, and instruct constants out of `omnivoice/app.py`.
- [x] Move device/dtype selection out of `omnivoice/app.py`.
- [x] Move model loading and model cache logic out of `omnivoice/app.py`.
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

- [x] Update `omnivoice/omnivoice_cli.py` to use backend core.
- [x] Remove duplicated `VALID_INSTRUCTS_EN/ZH` from CLI.
- [x] Remove duplicated `pick_device` from CLI if core owns it.
- [x] Remove duplicated `load_voice_clone_prompt` from CLI if core owns it.
- [ ] Verify `speaker-id` command still works.
- [ ] Verify `ref-audio` command still works.
- [ ] Verify `voice-design` command still works.
- [ ] Update README if command usage or behavior changes.

## Phase 3: Voice Profiles v1

- [ ] Create `VoiceProfileStore` abstraction.
- [ ] Keep backward compatibility with `speakers.json`.
- [ ] Standardize profile fields: `id`, `name`, `type`, `prompt_path`, `language`.
- [ ] Add metadata fields: `ref_text`, `created_at`, `updated_at`.
- [ ] Add `list_profiles()`.
- [ ] Add `get_profile(id)`.
- [ ] Add `create_profile(...)`.
- [ ] Add `rename_profile(...)`.
- [ ] Add `delete_profile(...)`.
- [ ] Update UI speaker dropdown to use profile store.
- [ ] Update CLI speaker-id mode to use profile store.

## Phase 4: OpenAI-Compatible Speech API

- [ ] Add FastAPI/uvicorn dependencies if missing.
- [ ] Create a separate FastAPI app, for example `api_server.py`.
- [ ] Add `/health`.
- [ ] Add `/v1/models`.
- [ ] Add `/v1/voices`.
- [ ] Add `/v1/audio/speech`.
- [ ] Map OpenAI-style requests into backend core generation requests.
- [ ] Return WAV or another initially supported audio format.
- [ ] Add README section for running the API server.
- [ ] Smoke test `/health`.

## Phase 5: Basic Model Status and Install UI

- [ ] Extract model status helpers from `model_store.py`.
- [ ] Report model status: installed or missing.
- [ ] Check `config.json`.
- [ ] Check weight files.
- [ ] Show local model path.
- [ ] Add model status to UI or API.
- [ ] Add install/download action for missing model.
- [ ] Add minimal progress/log output for download.

## Phase 6: Generation History

- [ ] Choose initial storage: SQLite or JSONL.
- [ ] Save metadata for each generation.
- [ ] Save mode: `speaker-id`, `ref-audio`, `voice-design`.
- [ ] Save model id/source.
- [ ] Save generation params.
- [ ] Save output path.
- [ ] Add history listing helper/API.
- [ ] Add basic history UI.

## Phase 7: Audio DSP Presets

- [ ] Split raw generation and audio post-processing into separate steps.
- [ ] Add preset `raw`.
- [ ] Add preset `normalize`.
- [ ] Add preset `broadcast`.
- [ ] Add effect preset option to UI.
- [ ] Add effect preset option to CLI/API.

## Later Features

- [ ] ASR transcription.
- [ ] OpenAI-compatible transcription endpoint.
- [ ] Translation provider registry.
- [ ] Subtitle import/export.
- [ ] Video dubbing.
- [ ] Realtime dictation.
- [ ] Speaker diarization.
- [ ] Batch queue.
- [ ] Voice gallery.
- [ ] Watermarking.
- [ ] MCP server.
- [ ] Marketplace/import/export.
- [ ] Desktop packaging with Tauri/React.

## Done Log

- [x] Created initial refactor and feature tracking plan.
- [x] Completed Phase 1 backend core extraction: `omnivoice_core.py` owns generation, model, prompt, and speaker registry logic; `omnivoice/app.py` now only builds the Gradio UI.
- [x] Refactored CLI to use `omnivoice_core.py` for model loading, instruct parsing, speaker registry loading, and prompt loading. CLI help was smoke tested for all subcommands.
