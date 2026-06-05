# OmniVoice Studio Feature Specification for omnivoice-kit

This document describes the product features present in OmniVoice Studio and
the technology/model choices behind them. It is intended as a feature reference
for planning `omnivoice-kit`, not as a code structure guide.

## Product Summary

OmniVoice Studio is a local-first AI voice workstation. It focuses on:

- Text-to-speech generation.
- Zero-shot voice cloning.
- Voice design from natural-language speaker attributes.
- Local video dubbing.
- Realtime dictation.
- Voice profile management.
- Model management.
- OpenAI-compatible audio APIs.
- Desktop packaging for macOS, Windows, and Linux.

The product is designed around privacy and local execution: user audio,
generated speech, voice profiles, logs, and project data stay on the user's
machine unless the user explicitly configures an online translation or LLM
provider.

## Technology Overview

| Area | Technology |
|---|---|
| Desktop app | Tauri 2, Rust |
| Frontend app | React 19, Vite 8 |
| Video editor workspace | OpenCut upstream (`video-editor/`), Bun + Turbo |
| Frontend state | Zustand, TanStack Query |
| Data-heavy UI | TanStack Table, TanStack Virtual |
| UI primitives | Radix UI, lucide-react, TailwindCSS 4 |
| Backend API | Python FastAPI |
| Realtime communication | WebSocket, Server-Sent Events |
| Local database | SQLite |
| Python environment | uv |
| JavaScript runtime/package manager | Bun |

Current `video-editor/` integration status: OpenCut rewrite route `/` contains an OmniVoice backend test panel for backend URL settings, health/memory diagnostics, model unload, file transcription, and emotion-script TTS preview/download. Full timeline integration is pending.
| Audio processing | torchaudio, soundfile, pydub, pedalboard |
| Video/audio processing | FFmpeg |
| ML runtime | PyTorch, transformers, CTranslate2 |
| Speech recognition | WhisperX, faster-whisper, MLX Whisper, PyTorch Whisper |
| Speaker diarization | pyannote.audio |
| Model downloads/cache | HuggingFace Hub |
| Desktop distribution | Tauri MSI/NSIS/DMG/AppImage/deb |

## Model Overview

### Required Models

| Model | Purpose | Notes |
|---|---|---|
| `k2-fsa/OmniVoice` | Main TTS and voice cloning model | 600+ languages, zero-shot voice cloning/design, about 2.4 GB |
| `Systran/faster-whisper-large-v3` | Default ASR model | Cross-platform transcription, about 2.9 GB |

### Optional ASR Models

| Model | Purpose | Notes |
|---|---|---|
| `mlx-community/whisper-large-v3-mlx` | ASR | Apple Silicon MLX speedup |
| `mlx-community/whisper-large-v3-turbo` | ASR | Faster Apple Silicon dictation model |
| `openai/whisper-large-v3` | ASR | PyTorch/CUDA fallback |
| `mlx-community/whisper-tiny-mlx` | ASR | Fast Apple Silicon fallback |
| `Systran/faster-whisper-large-v3-turbo` | ASR | Faster large-v3 variant |
| `Systran/faster-distil-whisper-large-v3` | ASR | Distilled large-v3 |
| `Systran/faster-whisper-medium` | ASR | Balanced lower-VRAM option |
| `Systran/faster-whisper-small` | ASR | Fast preview and low VRAM |
| `Systran/faster-whisper-base` | ASR | Minimal Whisper option |
| `nvidia/parakeet-tdt-0.6b-v3` | ASR | NVIDIA CUDA-oriented ASR |
| `nvidia/parakeet-tdt-0.6b-v2` | ASR | NVIDIA English-oriented ASR |
| `UsefulSensors/moonshine-base` | ASR | Edge-optimized ONNX ASR |
| `UsefulSensors/moonshine-small` | ASR | Larger Moonshine ONNX ASR |

### Diarization Model

| Model | Purpose | Notes |
|---|---|---|
| `pyannote/speaker-diarization-3.1` | Speaker diarization | Multi-speaker detection, requires accepted HuggingFace license/token |

### Optional TTS Models and Engines

| Model/engine | Purpose | Notes |
|---|---|---|
| `OpenMOSS-Team/MOSS-TTS-Nano-100M` | Lightweight TTS | 20 languages, CPU realtime |
| `KittenML/kitten-tts-mini-0.8` | Lightweight English TTS | 8 preset voices, CPU realtime |
| `mlx-community/Kokoro-82M-bf16` | MLX-Audio TTS | Apple Silicon only |
| `mlx-community/csm-1b-8bit` | MLX-Audio voice cloning | Apple Silicon only |
| `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit` | MLX-Audio voice design | Apple Silicon only |
| `mlx-community/Dia-1.6B` | Expressive TTS | Apple Silicon only |
| `mlx-community/Llama-OuteTTS-1.0-1B-4bit` | Voice clone TTS | Apple Silicon only |
| `mlx-community/Chatterbox-TTS-4bit` | TTS | Apple Silicon only |
| `mlx-community/MeloTTS-English-v3-MLX` | English TTS | Apple Silicon only |
| CosyVoice 3 | Multilingual zero-shot TTS | 9 languages + dialects, optional engine |
| VoxCPM2 | Voice design / TTS | Optional engine |
| GPT-SoVITS | External TTS server integration | Optional external API server |
| Sherpa-ONNX | ONNX TTS runtime | Useful for CPU/edge/WASM-oriented future |
| IndexTTS2 | Isolated subprocess TTS | Optional engine |
| Supertonic3 | ONNX TTS | Optional CPU engine |

### GGUF Runtime

The project also has an OmniVoice GGUF path.

| Item | Value |
|---|---|
| Source model | `Serveurperso/OmniVoice-GGUF` |
| Runtime | `omnivoice.cpp` |
| High VRAM quant | BF16 |
| Mid VRAM quant | Q8_0 |
| Low VRAM quant | Q4_K_M |
| CPU quant | Q4_K_M |

## Feature: Local Text-To-Speech

### User Value

Users can type text and generate speech locally without cloud APIs or usage
limits.

### Core Behavior

- User enters text.
- User selects language or leaves language on auto.
- User selects generation quality/speed parameters.
- App generates WAV audio.
- Generated output is saved to local history.
- User can replay, export, or reuse the generated audio.

### Controls

- Text prompt.
- Language.
- Diffusion steps.
- Guidance scale.
- Speed.
- Fixed duration.
- Seed.
- Denoise toggle.
- Postprocess toggle.
- Effect preset.
- Advanced sampling controls.

### Models

Primary model:

- `k2-fsa/OmniVoice`

Optional TTS engines:

- KittenTTS for lightweight English CPU speech.
- MOSS-TTS-Nano for lightweight multilingual CPU speech.
- MLX-Audio engines for Apple Silicon.
- CosyVoice, VoxCPM2, GPT-SoVITS, Sherpa-ONNX, IndexTTS2, Supertonic3.

### Tech Stack Used

- FastAPI for generation endpoint.
- PyTorch for model inference.
- torchaudio/soundfile for WAV output.
- pedalboard/audio DSP for mastering/effects.
- SQLite for generation history.
- React for generation UI.

## Feature: Voice Cloning

### User Value

Users can clone a voice from a short audio sample and synthesize new speech in
that voice.

### Core Behavior

- User uploads or records reference audio.
- User optionally provides transcript/reference text for the sample.
- User enters target speech text.
- App synthesizes the target text using the reference voice.
- User can save the voice as a reusable profile.

### Inputs

- Target text.
- Reference audio.
- Optional reference text.
- Language.
- Voice instruction.
- Seed.
- Generation parameters.

### Outputs

- Generated WAV.
- Generation history entry.
- Optional saved voice profile.

### Models

Primary:

- `k2-fsa/OmniVoice` zero-shot voice cloning.

Optional:

- CosyVoice.
- MLX-Audio CSM/OuteTTS variants.
- GPT-SoVITS if configured.

### Tech Stack Used

- React drag/drop upload and recording controls.
- FastAPI multipart upload.
- Local filesystem voice sample storage.
- SQLite voice profile metadata.
- PyTorch TTS inference.

## Feature: Voice Design

### User Value

Users can create a voice from a written description without uploading reference
audio.

### Core Behavior

- User writes the speech text.
- User describes the speaker with attributes.
- App generates a voice matching the description.
- User can save the generated style as a reusable voice profile.

### Supported Attribute Categories

- Gender: male, female.
- Age: child, teenager, young adult, middle-aged, elderly.
- Pitch: very low, low, moderate, high, very high.
- Style: whisper.
- English accent: American, British, Australian, Canadian, Indian, Chinese,
  Korean, Japanese, Portuguese, Russian.
- Chinese dialect: Henan, Shaanxi, Sichuan, Guizhou, Yunnan, Guilin, Jinan,
  Shijiazhuang, Gansu, Ningxia, Qingdao, Northeast.

### Models

Primary:

- `k2-fsa/OmniVoice`

Optional:

- `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-4bit`
- VoxCPM2

### Tech Stack Used

- React prompt UI.
- TTS instruction string passed into model generation.
- SQLite for saved designed voice profiles.

## Feature: Voice Profiles

### User Value

Users can save, organize, and reuse voices instead of re-uploading reference
audio every time.

### Core Behavior

- Create a profile from reference audio or voice design settings.
- Store profile name, language, reference text, instruction, seed, and audio.
- Lock a profile to preserve a stable generated/reference voice.
- Use the profile in TTS and dubbing.
- Delete or update profiles.

### Profile Types

- Clone profile: based on reference audio.
- Design profile: based on speaker description/instruction.
- Locked profile: profile with stable locked audio.

### Models

Profiles are model-agnostic metadata, but primarily serve:

- OmniVoice.
- Other TTS engines that accept reference audio or voice presets.

### Tech Stack Used

- SQLite metadata.
- Filesystem audio storage.
- React profile management UI.
- FastAPI profile endpoints.

## Feature: Multi-Engine TTS Selection

### User Value

Users can choose the best TTS engine for their hardware, language, latency, and
quality needs.

### Core Behavior

- App lists all known engines.
- Each engine reports whether it is available.
- Missing engines show install hints.
- User can select the active engine.
- App uses selected engine for future generation.

### Engine Categories

- Full multilingual zero-shot: OmniVoice.
- Lightweight CPU: KittenTTS, MOSS-TTS-Nano.
- Apple Silicon: MLX-Audio engines.
- External/server engines: GPT-SoVITS.
- ONNX/edge-oriented: Sherpa-ONNX, Supertonic3.
- Experimental or isolated: IndexTTS2, OmniVoice GGUF.

### Tech Stack Used

- Python engine registry.
- Availability probes.
- Settings UI.
- Persistent local settings.

## Feature: Audio DSP and Effects

### User Value

Generated speech sounds more polished and consistent without manual audio
editing.

### Core Behavior

- Normalize generated audio.
- Apply mastering.
- Apply optional effect presets.
- Support raw output mode for users who want unprocessed model audio.

### Effects

The project supports an effect preset concept, including a default broadcast
style and raw/no-processing mode.

### Models

No model required. This is DSP post-processing.

### Tech Stack Used

- torchaudio.
- soundfile.
- pedalboard.
- Custom audio DSP utilities.

## Feature: Long-Form TTS

### User Value

Users can synthesize long passages without manually splitting text and without
VRAM growing linearly with input length.

### Core Behavior

- App estimates generated duration.
- If text is too long, app splits it into chunks.
- Each chunk is generated separately.
- Chunks are combined into one output.

### Controls

- Target chunk duration.
- Chunk activation threshold.
- Speed or fixed duration.

### Models

Primary:

- `k2-fsa/OmniVoice`

### Tech Stack Used

- Text segmentation.
- TTS chunk generation.
- Audio concatenation.

## Feature: Video Dubbing

### User Value

Users can dub a video into another language locally, including transcription,
translation, synthetic speech, and final video export.

### Core Workflow

1. User uploads a video/audio file or ingests a URL.
2. App extracts source audio with FFmpeg.
3. App transcribes source speech.
4. App segments transcript into timestamped lines.
5. App optionally detects speakers.
6. User reviews/edits segments.
7. App translates segments into target language.
8. User assigns voices to speakers/segments.
9. App synthesizes translated speech per segment.
10. App time-fits generated audio to segment timings.
11. App mixes dubbed speech.
12. App exports audio, video, subtitles, or stems.

### Outputs

- Dubbed video.
- Dubbed audio.
- Segment previews.
- SRT subtitles.
- VTT subtitles.
- Stems/track exports.
- Project history.

### Models

ASR:

- WhisperX.
- faster-whisper large-v3.
- Optional Whisper variants.

Diarization:

- `pyannote/speaker-diarization-3.1`

TTS:

- Active TTS engine, usually OmniVoice.

Translation:

- Argos.
- NLLB-200.
- Google Translate through `deep_translator`.
- DeepL.
- Microsoft Translator.
- MyMemory.
- OpenAI-compatible LLM provider.

### Tech Stack Used

- FFmpeg for extraction, muxing, thumbnails, media conversion.
- FastAPI for long-running job endpoints.
- SSE/job events for progress.
- SQLite for job/history metadata.
- React segment editor.
- Waveform/video preview UI.

## Feature: Subtitle Import, Edit, and Export

### User Value

Users can correct transcription errors or use existing subtitles instead of
relying entirely on ASR.

### Core Behavior

- Import `.srt`.
- Parse subtitle cues.
- Validate timestamps.
- Clamp cues to media duration.
- Replace or update dub segments.
- Export generated subtitles as `.srt` or `.vtt`.

### Models

No model required for import/export. ASR is only used when generating subtitles
from audio.

### Tech Stack Used

- SRT parser.
- FastAPI file upload.
- React segment table/editor.

## Feature: Translation

### User Value

Users can translate dubbing segments with local or online providers.

### Core Behavior

- User selects translation provider.
- App checks provider availability.
- App translates segment text.
- App preserves timing and speaker metadata.
- App can use glossary terms to keep names/terms consistent.

### Providers

| Provider | Type | Notes |
|---|---|---|
| Argos | Offline | Local CPU translation, language packs downloaded per pair |
| NLLB-200 | Offline | Higher quality, heavier model |
| Google Translate | Online | Free web endpoint via `deep_translator`, rate-limited |
| DeepL | Online | Requires API key |
| Microsoft Translator | Online | Requires API key |
| MyMemory | Online | No key for limited use |
| OpenAI-compatible LLM | Online/local endpoint | Works with OpenAI, OpenRouter, Gemini compat, DeepSeek, Qwen, Ollama, LM Studio |

### Models

- NLLB-200 for local heavy translation.
- LLM model selected by the user for OpenAI-compatible provider.

### Tech Stack Used

- Translation provider registry.
- Python provider adapters.
- Settings UI for keys/provider state.

## Feature: ASR Transcription

### User Value

Users can convert audio/video speech into text with timestamps.

### Core Behavior

- User uploads audio/video.
- App converts/extracts audio if needed.
- App transcribes speech.
- App returns full text and timestamped segments.
- App can return word-level timing when supported.

### Output Formats

- JSON.
- Plain text.
- Verbose JSON.
- SRT.
- VTT.

### Models

Primary:

- WhisperX with faster-whisper.
- `Systran/faster-whisper-large-v3`

Optional:

- MLX Whisper on Apple Silicon.
- PyTorch Whisper fallback.
- Other faster-whisper sizes.
- Parakeet.
- Moonshine ONNX.

### Tech Stack Used

- FFmpeg/audio conversion.
- WhisperX/faster-whisper.
- CTranslate2.
- FastAPI upload endpoints.

## Feature: Speaker Diarization

### User Value

Users can separate who spoke when in multi-speaker content, which improves
dubbing voice assignment.

### Core Behavior

- App runs diarization on source audio.
- App assigns speaker labels to segments.
- User can map speakers to voice profiles.

### Models

- `pyannote/speaker-diarization-3.1`

### Requirements

- HuggingFace token.
- License acceptance for pyannote model.

### Tech Stack Used

- pyannote.audio.
- Segment assignment logic.
- Speaker-to-voice UI.

## Feature: Realtime Dictation

### User Value

Users can dictate text from the microphone and get partial/final transcription
locally.

### Core Behavior

- User opens capture widget or floating pill.
- App records microphone audio.
- Audio chunks stream to backend.
- Backend returns partial transcript updates.
- Backend returns final transcript after silence or stop.
- App can auto-paste final text into the active application.

### Models

- Active ASR backend.
- Faster Whisper large-v3 by default.
- MLX Whisper Turbo is preferred for fast Apple Silicon dictation when
  available.

### Tech Stack Used

- Tauri floating window.
- WebSocket audio streaming.
- Browser/desktop microphone capture.
- ASR backend.

## Feature: Batch Queue

### User Value

Users can process multiple generation or dubbing tasks without manually waiting
for each one.

### Core Behavior

- User enqueues batch jobs.
- App tracks pending/running/completed/failed states.
- User can inspect job progress.
- User can cancel/delete jobs.
- User can download completed outputs.

### Models

- Active TTS/ASR/translation engines depending on job type.

### Tech Stack Used

- Local job queue.
- SQLite job metadata.
- SSE or polling for progress.
- React batch queue UI.

## Feature: Voice Gallery

### User Value

Users can browse, search, organize, and reuse voice assets.

### Core Behavior

- List saved/imported voices.
- Search by name/category/tag.
- Favorite voices.
- Upload custom voice audio.
- Download/import voices.
- Convert gallery voice into a generation profile.

### Models

No model required for gallery management. TTS models are used when previewing
or generating with a selected voice.

### Tech Stack Used

- SQLite metadata.
- Filesystem audio storage.
- React virtualized/searchable gallery.

## Feature: Model Store and Setup Wizard

### User Value

Users can see which models are required, which are installed, and download
missing models with progress feedback.

### Core Behavior

- App runs preflight checks.
- App lists recommended models for the current platform/hardware.
- App shows installed/missing status.
- User can install, reinstall, or delete models.
- App streams download progress.
- App performs warmup checks.

### Models

Uses the full model catalog described above.

### Tech Stack Used

- HuggingFace Hub.
- YAML model catalog.
- SSE progress stream.
- React model table.
- Local cache detection.

## Feature: Settings

### User Value

Users can configure engines, models, credentials, performance, capture, logs,
privacy, and appearance in one place.

### Settings Areas

- Models.
- TTS/ASR/translation engines.
- Capture/dictation.
- API credentials.
- Performance.
- Logs.
- About/version.
- Privacy.
- Appearance.

### Key Behaviors

- Select active TTS engine.
- View engine compatibility and missing dependencies.
- Save API keys securely.
- View backend/frontend/Tauri logs.
- Clear logs.
- Flush/unload models from memory.
- See system/GPU information.

### Tech Stack Used

- React settings tabs.
- FastAPI system/settings endpoints.
- SQLite/encrypted settings storage.
- Local log files.

## Feature: Logs and Diagnostics

### User Value

Users can diagnose model download, generation, ASR, dubbing, and desktop issues
without opening a terminal.

### Core Behavior

- Show backend logs.
- Show frontend logs.
- Show Tauri logs.
- Support refresh/filter/clear.
- Redact sensitive tokens.
- Surface friendly error messages and docs links.

### Models

No model required.

### Tech Stack Used

- Python logging with rotating file handler.
- Frontend console buffer.
- Tauri log reading.
- Token redaction filter.

## Feature: OpenAI-Compatible Audio API

### User Value

Developers can use OmniVoice through familiar OpenAI-style endpoints.

### Core Behavior

- Generate speech through a `/speech` style endpoint.
- Transcribe audio through a `/transcriptions` style endpoint.
- List available voices.
- Use profile IDs as voice IDs.
- Return audio in common formats.

### Supported Capabilities

- Text-to-speech.
- Speech-to-text.
- Voice listing.
- Voice profile integration.
- Model/engine alias mapping.

### Models

- Active TTS backend.
- Active ASR backend.

### Tech Stack Used

- FastAPI compatibility router.
- Pydantic request/response schemas.
- Audio encoding utilities.

## Feature: MCP Server

### User Value

AI agents and MCP clients can call OmniVoice voice tools directly.

### Core Behavior

- Expose speech generation as a tool.
- List voices.
- List languages.
- List personality presets.
- Check backend health.
- Expose recent generation history as a resource.

### Models

- Active TTS backend.

### Tech Stack Used

- MCP Python SDK.
- HTTP calls into local backend.

## Feature: Export and File Management

### User Value

Users can export generated media and open output locations from the desktop app.

### Core Behavior

- Export generated audio.
- Export dubbed video/audio.
- Export subtitles.
- Export stems.
- Record export history.
- Reveal destination in OS file manager.

### Models

No model required at export time, unless export triggers generation first.

### Tech Stack Used

- FFmpeg.
- Local filesystem.
- Tauri OS integration.
- SQLite export history.

## Feature: Marketplace and Voice Package Import/Export

### User Value

Users can move voice profiles between installs or share packaged voices.

### Core Behavior

- Export a profile package.
- Import a profile package.
- Browse local/shared packages.
- Install a package as a profile.
- Delete packages.

### Package Contents

- Profile metadata.
- Reference/locked audio.
- Preview audio.
- Optional license/attribution metadata.

### Models

No model required for package management. TTS model is used for preview or
generation after install.

### Tech Stack Used

- Zip packaging.
- JSON metadata.
- Filesystem storage.
- SQLite profile insertion.

## Feature Priority for omnivoice-kit

### Must Have

- Local TTS generation.
- Voice cloning.
- Voice design.
- Voice profiles.
- TTS engine selection.
- OpenAI-compatible speech endpoint.
- Basic model status/install UI.

### Should Have

- ASR transcription.
- OpenAI-compatible transcription endpoint.
- Translation provider registry.
- Audio DSP/effect presets.
- Generation history.
- Settings and diagnostics.

### Could Have

- Video dubbing.
- Realtime dictation.
- Speaker diarization.
- Batch queue.
- Voice gallery.
- MCP server.
- Marketplace/import/export.

### Later

- Desktop packaging.
- Auto-updater.
- Hosted/server deployment.
- Plugin marketplace.
