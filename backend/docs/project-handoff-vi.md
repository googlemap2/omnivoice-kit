# OmniVoice Kit - tài liệu handoff dự án

Tài liệu này dành cho agent hoặc dev ở session khác. Hãy đọc file này trước khi sửa code để nắm nhanh mục tiêu sản phẩm, kiến trúc, tech stack, model, luồng thực hiện và các tính năng đã có.

## 1. Mục tiêu sản phẩm

`omnivoice-kit` là một studio AI voice chạy local-first, tập trung vào:

- Tạo giọng nói từ văn bản bằng OmniVoice.
- Clone giọng zero-shot từ audio mẫu.
- Tạo giọng theo mô tả/voice design.
- Quản lý voice profile dùng lại qua `speaker_id`.
- Transcribe audio/video sang text, JSON, SRT, VTT.
- Dịch text/segment bằng provider registry.
- Dubbing audio/video: tách âm thanh, ASR, dịch, TTS từng segment, ghép audio/video.
- Realtime dictation qua WebSocket.
- Batch queue cho tác vụ dài.
- API tương thích OpenAI cho speech/transcription.
- Frontend Next.js dạng studio UI.

Định hướng chính là privacy/local-first: audio, profile, output, settings và model cache nằm trong project/local machine, trừ khi người dùng tự cấu hình provider online.

## 2. Tech stack hiện tại

Backend:

- Python package: `backend/`
- API: FastAPI trong `backend/api.py`
- CLI: `backend/cli.py`, chạy bằng `uv run backend ...`
- TTS runtime: `omnivoice`, PyTorch
- Audio IO/DSP: `soundfile`, `numpy`, `torchaudio`/DSP helper trong `backend/audio.py`
- ASR: `faster-whisper`
- Video/audio processing: FFmpeg wrapper trong `backend/media.py`
- Diarization: optional `pyannote.audio`
- Database/job/history: PostgreSQL qua Supabase nếu có `VOICEKIT_DATABASE_URL`
- Local settings: JSON tại `data/settings.json`
- Model download/cache: Hugging Face Hub, lưu trong `models/`

Frontend:

- Next.js 15 App Router, React 19
- UI: MUI 6 (`@mui/material`, `@mui/icons-material`)
- State orchestration: React context trong `frontend/src/components/studio/StudioContext.tsx`
- API client: `frontend/src/lib/api.ts`
- Studio pages: `frontend/src/app/(studio)/*`

Package/runtime:

- Python: `uv`
- Frontend package manager: `pnpm`
- Dev frontend: `pnpm dev`
- Build frontend: `pnpm build`

## 3. Model và cache

Model chính:

- TTS/voice clone/voice design: `k2-fsa/OmniVoice`
- ASR mặc định: `Systran/faster-whisper-large-v3`
- Diarization mặc định trong code hiện tại: `pyannote/speaker-diarization-community-1`

Model store:

- Model được tải vào thư mục `models/` của project.
- Ví dụ:
  - `models/models--k2-fsa--OmniVoice/`
  - `models/models--Systran--faster-whisper-large-v3/`
  - `models/models--pyannote--speaker-diarization-community-1/`
- Cache phụ Hugging Face: `models/.hf_home/hub/`

API liên quan model:

- `GET /v1/model-status`
- `POST /v1/model-status/install`
- `GET /v1/models`

## 4. Cấu trúc backend quan trọng

- `backend/app/main.py`: FastAPI app shell, CORS, startup/shutdown worker hooks, router registration. Public entrypoint `backend.app.main:app` remains stable.
- `backend/app/routers/`: API routers split by topic. Core workflow endpoints live in focused routers such as `speech.py`, `transcription.py`, `subtitles.py`, `translation.py`, `dubbing.py`, `diarization.py`, `dictation.py`, `voices.py`, `jobs.py`, and `settings.py`; `workflows.py` remains as an empty compatibility router during the transition.
- `backend/app/schemas/`: Pydantic request schemas grouped by feature.
- `backend/services/`: real service implementations for speech, emotion TTS, transcription, subtitles, translation, dubbing, diarization, dictation, voice profiles, models, and diagnostics.
- `backend/infrastructure/`: real infrastructure implementations for Hugging Face/model store, database, media, logging, and database-backed stores.
- `backend/domain/`: domain-level primitives/config such as audio presets and local settings.
- `backend/api.py`: compatibility shim exporting the FastAPI app.
- `backend/core.py`, `backend/asr.py`, `backend/subtitles.py`, `backend/translation.py`, `backend/dubbing.py`, `backend/diarization.py`, `backend/dictation.py`, `backend/emotion_tts.py`, `backend/profiles.py`, `backend/diagnostics.py`: compatibility aliases to `backend/services/*`.
- `backend/model_store.py`, `backend/database.py`, `backend/media.py`, `backend/stores/*`: compatibility aliases to `backend/infrastructure/*`.
- `backend/audio.py`, `backend/settings.py`: compatibility aliases to `backend/domain/*`.
- Internal imports should use `backend/services/*`, `backend/domain/*`, and `backend/infrastructure/*` directly instead of root compatibility shims.
- `backend/cli/`: CLI package shell; legacy command implementation remains in `backend/cli_legacy.py`.
- `backend/mcp/`: MCP server package; `backend/mcp_server.py` remains a compatibility alias.
- `backend/legacy/ui.py`: Gradio legacy UI; `backend/ui.py` remains a compatibility alias.
- `backend/scripts/`: standalone utility scripts.

## 5. Cấu trúc frontend quan trọng

- `frontend/src/lib/api.ts`: helper `apiJson`, `apiForm`, `apiAudio`, `apiWebSocketUrl`, tự thêm header `ngrok-skip-browser-warning`.
- `frontend/src/components/studio/StudioContext.tsx`: state chính và action gọi backend cho Speech, Transcription, Translation, Dubbing, Jobs, Voices, Settings.
- `frontend/src/components/layout/Explorer.tsx`: sidebar Explorer có nút collapse/expand; width được điều khiển bởi state trong `StudioFrame`.
- Layout frontend responsive: trên mobile `ActivityBar` chuyển xuống dưới như bottom navigation, `Explorer` bị ẩn, các workspace grid chuyển về một cột; desktop giữ layout sidebar/explorer/editor.
- `frontend/src/app/(studio)/speech/page.tsx`: UI tạo speech, gồm các mode:
  - `emotion`: kịch bản cảm xúc bằng tag inline; đây là tab đầu tiên trên UI Speech, thay cho tab `Saved Voice`.
  - `clone`: upload reference audio.
  - `design`: voice design bằng instruct items.
  - `speaker`: vẫn là mode/API/CLI nội bộ dùng voice profile/speaker id, nhưng không còn tab riêng trên UI Speech.
- `frontend/src/app/(studio)/transcription/page.tsx`: upload audio/video, ASR, subtitle editor/import/export, dictation.
- `frontend/src/app/(studio)/translation/page.tsx`: dịch text/segments.
- `frontend/src/app/(studio)/dubbing/page.tsx`: dubbing audio/video, diarization, speaker voice map.
- `frontend/src/app/(studio)/jobs/page.tsx`: list/cancel/delete/download job.
- `frontend/src/app/(studio)/voices/page.tsx`: tạo/list voice profile.
- `frontend/src/app/(studio)/settings/page.tsx`: model/settings/provider keys.
- `frontend/src/types/api.ts`: shared API types.
- `frontend/src/types/studio.ts`: workspace/mode types.

## 6. Luồng chạy local

Backend:

```bash
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
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

Nếu backend chạy qua ngrok/Colab, đặt `NEXT_PUBLIC_API_BASE_URL` thành URL backend ngrok. Nếu frontend chạy từ origin khác localhost, cần set backend env:

```bash
VOICEKIT_CORS_ORIGINS=http://localhost:3000,https://your-frontend-origin.example
```

## 7. Speech/TTS flow

### Speaker ID

Frontend:

- Page: `frontend/src/app/(studio)/speech/page.tsx`
- Action: `studio.generateSpeech()`
- Context: `frontend/src/components/studio/StudioContext.tsx`
- Endpoint: `POST /v1/audio/speech`

Backend:

- Request model: `SpeechRequest`
- Function: `generate_clone_with_speaker_id()` trong `backend/core.py`
- Load profile từ `VoiceProfileStore`.
- Load prompt `.pt` hoặc `.npy`.
- Gọi `model.generate(...)`.
- Apply effect preset.
- Trả WAV.

CLI:

```bash
uv run backend speaker-id --speaker_id yen --text "Xin chào" --output out.wav
```

### Clone by Reference Audio

Frontend gửi multipart form đến:

- `POST /v1/audio/speech/clone`

Backend:

- Lưu upload tạm hoặc vào `data/uploads` nếu queued.
- Gọi `generate_clone_with_ref_audio()` trong `backend/core.py`.

CLI:

```bash
uv run backend ref-audio --ref_audio path/to/ref.wav --ref_text "..." --text "..." --output out.wav
```

### Voice Design

Endpoint:

- `POST /v1/audio/speech/design`

Backend:

- `generate_voice_design()` trong `backend/core.py`
- Bắt buộc có `instruct_items`.

CLI:

```bash
uv run backend voice-design --text "..." --instruct-item female --instruct-item middle-aged --output out.wav
```

## 8. Kịch bản cảm xúc theo từng câu

Tính năng này cho phép người dùng viết text có tag cảm xúc inline, ví dụ:

```text
[thoughtful] Chọn xong mấy em soạn kịch bản nhé.
[whisper] Các vợ kéo xuống cuối.
[excited] Bấm vào cho anh nha.
```

Frontend UX:

- Tab: `Emotion Script` trong `frontend/src/app/(studio)/speech/page.tsx`.
- Speech workspace không còn hiển thị section `Voices` trong `Explorer`; chọn voice vẫn nằm trong panel bên phải của Speech page.
- Trang Speech dùng tiếng Anh cho UI copy; riêng label trong emotion tag picker và option label của `Voice instruct` vẫn dùng tiếng Việt có dấu để người dùng chọn cảm xúc/chỉ dẫn dễ hơn.
- Người dùng gõ `@` để mở list tag tiếng Việt.
- UI hiển thị label tiếng Việt nhưng chèn value kỹ thuật vào text:
  - `Suy tư` -> `[thoughtful]`
  - `Cười khúc khích` -> `[chuckles]`
  - `Thì thầm` -> `[whisper]`
  - `Ngạc nhiên` -> `[surprised]`
  - `Hào hứng` -> `[excited]`
  - `Đang cười` -> `[laughing]`
- Lưu ý quan trọng: tiếng Việt chỉ là label hiển thị; backend nhận tag tiếng Anh trong dấu `[]` và instruct value gốc như `female`, `high pitch`, `whisper`.

Frontend flow:

- `emotionTags` chứa `{ id, label }`.
- List hiển thị `tag.label`.
- Khi click, `insertEmotionTag(tag.id)` chèn `[${tag.id}]`.
- `StudioContext.generateSpeech()` gọi endpoint:

```text
POST /v1/audio/speech/emotion-script
```

- Nếu bật `Send to queue`, frontend gửi `queued: true`; backend tạo job `speech` với `mode: "emotion"` và worker ghi WAV vào `outputs/jobs`.

Backend flow:

- API model: `EmotionSpeechRequest` trong `backend/api.py`.
- Endpoint: `create_emotion_script_speech()`.
- Queue worker: `backend/jobs.py` xử lý `speech` job mode `emotion` bằng `render_emotion_tts_speaker_id()`.
- Parser nhận tag dạng `[tag]` hoặc `(tag)`.
- Mapping mặc định trong `DEFAULT_TAG_ALIASES`:
  - `whisper` -> `whisper`
  - `excited` -> `high pitch`
  - `surprised` -> `very high pitch`
  - `thoughtful` -> `moderate pitch`
  - `laughing` -> `high pitch`
  - `chuckles` -> `high pitch`
- Mỗi segment được generate riêng với cùng `voice_clone_prompt`, sau đó ghép audio bằng `numpy.concatenate`.
- Có khoảng nghỉ giữa segment qua `gap_ms`.

CLI:

```bash
uv run backend emotion-script \
  --speaker_id yen \
  --script "[thoughtful] Chọn xong mấy em soạn kịch bản nhé. [whisper] Các vợ kéo xuống cuối. [excited] Bấm vào cho anh nha." \
  --output out_emotion.wav \
  --language vi
```

Giới hạn hiện tại:

- Đây là v1, chưa phải emotion embedding native của model.
- Tag cảm xúc được map thành OmniVoice `instruct`.
- Các tag như `laughing/chuckles` hiện map sang `high pitch`; nếu cần cười thật tự nhiên hơn, cần model/prompt strategy tốt hơn hoặc thêm audio cue/postprocess.

## 9. Voice profiles và speaker_id

Voice profile là cách lưu một giọng để dùng lại.

File/module:

- `speakers.json` ở root vẫn được hỗ trợ để tương thích cũ.

Field profile chuẩn:

- `id`
- `name`
- `type`
- `prompt_path`
- `language`
- `ref_text`
- `tags`
- `favorite`
- `notes`
- `preview_path`
- `asset_dir`
- `created_at`
- `updated_at`

Profile cũ trong `speakers.json` được normalize tự động khi đọc. Nếu thiếu metadata gallery, `VoiceProfileStore` sẽ dùng default an toàn: `tags=[]`, `favorite=false`, `asset_dir=assets/voices/{voice_id}`.

Tạo prompt từ audio:

```bash
python -m backend.scripts.build_speaker_prompt \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chào đây là mẫu giọng" \
  --out assets/speakers/my_voice.pt
```

Tạo/list/delete/rename qua API:

- `GET /v1/voices`
- `POST /v1/voices`
- `DELETE /v1/voices/{voice_id}`
- `POST /v1/voices/{voice_id}/rename`

Voice Gallery v1:

- Helper backend: `VoiceProfileStore.search_profiles()`.
- API mới: `GET /v1/voice-profiles`, `GET /v1/voice-profiles/{voice_id}`, `POST /v1/voice-profiles`, `PATCH /v1/voice-profiles/{voice_id}`, `DELETE /v1/voice-profiles/{voice_id}`.
- Preview/export: `POST /v1/voice-profiles/{voice_id}/preview`, `GET /v1/voice-profiles/{voice_id}/export`.
- UI `frontend/src/app/(studio)/voices/page.tsx` có search local, filter favorites, toggle favorite, delete profile, generate preview, export metadata.

## 10. ASR transcription

Module:


Endpoint:

- `POST /v1/audio/transcriptions`

Input:

- Multipart `file`
- `model`
- `language`
- `response_format`
- `queued`

## 10.1 Logs và diagnostics

- Module: `backend/diagnostics.py`.
- Log file mặc định: `data/logs/backend.log`.
- Có `RotatingFileHandler` và redaction cho token/API key/secret/password.
- API:
  - `GET /v1/diagnostics`
  - `GET /v1/logs?limit=200`
  - `DELETE /v1/logs`
- Diagnostics gồm system info, Python executable, torch/CUDA/MPS status, ffmpeg/ffprobe, model cache path/status/size.
- UI: tab `Diagnostics` trong `frontend/src/app/(studio)/settings/page.tsx`.

Output formats:

- `json`
- `text`
- `verbose_json`
- `srt`
- `vtt`

CLI:

```bash
uv run backend transcribe --input path/to/audio.wav --language vi --format verbose_json
```

Frontend:

- `frontend/src/app/(studio)/transcription/page.tsx`
- `StudioContext.transcribe()`
- The Transcription page has two local tabs:
  - `ASR`: media transcription, dictation, transcript translation, and raw/translated subtitle artifact downloads.
  - `Subtitle Tools`: import SRT/VTT, edit subtitle segments, and export SRT/VTT.

Transcription translation:

- The Transcription page has a `Translate` switch.
- When enabled, translation can use either the existing translation provider registry or a configured OpenAI-compatible Model Provider from Settings.
- During ASR, translation is handled inside `POST /v1/audio/transcriptions`; the frontend does not make a separate `/v1/translation/translate` call for transcript translation.
- Model Provider translation sends `provider_model_id` and optional `provider_model_name` to the transcription endpoint.
- When `response_format` is `srt` or `vtt` and `Translate` is enabled, the transcription endpoint can return raw and translated subtitle artifacts in one JSON response.
- The Transcription page exposes download buttons for raw and translated subtitle files matching the selected `srt` or `vtt` output format.
- Queued transcription jobs use the same translation path and expose raw/translated subtitle artifacts in the job result.

## 11. Subtitle import/export

Module:

- `backend/subtitles.py`

Endpoints:

- `POST /v1/subtitles/import`
- `POST /v1/subtitles/export`

CLI:

```bash
uv run backend subtitle-import --input transcript.srt --output segments.json
uv run backend subtitle-export --input segments.json --format vtt --output transcript.vtt
```

Segment shape:

- `id`
- `start`
- `end`
- `text`
- `speaker`
- `metadata`

## 12. Translation

Module:

- `backend/translation.py`

Provider registry hiện có:

- `passthrough`: giữ nguyên text, dùng để test pipeline.
- `google`: qua `deep-translator`, có config disabled.
- `nllb`: local transformer model nếu dependency/model có sẵn.
- `deepl`, `microsoft`, `mymemory`: có placeholder/config API key.

Endpoints:

- `GET /v1/translation/providers`
- `POST /v1/translation/translate`

CLI:

```bash
uv run backend translate --text "Xin chào" --source-language vi --target-language en --provider passthrough
```

Settings provider:

- Lưu ở `data/settings.json`.
- API:
  - `GET /v1/settings`
  - `PUT /v1/settings`
  - `PATCH /v1/settings/translation-providers`

## 13. Dubbing

Module:

- `backend/dubbing.py`
- FFmpeg helper: `backend/media.py`

Pipeline:

1. Nhận audio/video input.
2. Extract audio bằng FFmpeg.
3. ASR thành segments.
4. Optional diarization rồi merge speaker label.
5. Translate segments.
6. Gán voice profile cho toàn bộ segment hoặc theo `speaker_voice_map`.
7. Generate TTS từng segment bằng `generate_clone_with_speaker_id()`.
8. Fit audio vào timing segment bằng padding/trimming đơn giản.
9. Mix dubbed WAV.
10. Export SRT/VTT.
11. Nếu input có video, mux dubbed audio với video stream.

Endpoints:

- `POST /v1/dubbing/dub`
- `POST /v1/dubbing/dub-upload`

CLI:

```bash
uv run backend dub \
  --input path/to/video.mp4 \
  --voice yen \
  --source-language en \
  --target-language vi \
  --provider passthrough \
  --output-dir outputs/dubbing
```

Frontend:

- `frontend/src/app/(studio)/dubbing/page.tsx`
- `StudioContext.runDubbing()`

## 14. Speaker diarization

Module:


Model:

- `pyannote/speaker-diarization-community-1`

Yêu cầu:

- Cài `pyannote.audio`.
- Có Hugging Face token trong `data/settings.json` hoặc env `HF_TOKEN`/`HUGGINGFACE_TOKEN`.
- Người dùng phải accept license/user conditions trên Hugging Face.

Endpoints:

- `GET /v1/diarization/status`
- `POST /v1/diarization/diarize`
- `POST /v1/diarization/merge`

CLI:

```bash
uv run backend diarize --input path/to/audio.wav --output speakers.json
```

## 15. Realtime dictation

Module:


Endpoint:

- `GET /v1/dictation/status`
- `WS /v1/dictation/ws`

Protocol:

- Client mở WebSocket.
- Gửi JSON `{"type":"start","mime_type":"..."}`
- Stream audio chunks dạng bytes.
- Gửi JSON `{"type":"stop"}` để chốt transcript.
- Server trả event `ready`, `partial`, `final`, `done`, `error`.

Frontend:

- Browser microphone capture bằng `MediaRecorder`.
- Action nằm trong `StudioContext.startDictation()` và `stopDictation()`.

Giới hạn hiện tại:

- V1 dùng stop thủ công.
- Chưa có silence/end-of-utterance detection hoàn chỉnh.

## 16. Batch queue/jobs

Module:

- `backend/jobs.py`

Job types:

- `speech`
- `transcription`
- `translation`
- `dubbing`

States:

- `pending`
- `running`
- `completed`
- `failed`
- `canceled`

Database:

- PostgreSQL/Supabase qua env `VOICEKIT_DATABASE_URL`.
- Nếu không có DB hoặc DB lỗi, một số helper có fallback/ghi log tùy module.

Endpoints:

- `GET /v1/jobs`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/cancel`
- `DELETE /v1/jobs/{job_id}`

Frontend:

- `frontend/src/app/(studio)/jobs/page.tsx`
- Download output qua `GET /v1/files?path=...`

## 17. Generation history

Module:

- `backend/history.py`

Endpoint:

- `GET /v1/generation-history`

Lưu metadata:

- mode
- model
- text
- voice
- language
- params
- output path
- status

Lưu ý: một số path realtime trả WAV trực tiếp có thể không có output path đầy đủ nếu chưa ghi file ra disk.

## 18. Settings

Module:

- `backend/settings.py`

Path:

- `data/settings.json`

Fields chính:

- `default_model`
- `default_device`
- `default_effect_preset`
- `output_dir`
- `default_translation_provider`
- `translation_provider_config`
- `huggingface_token`

Endpoints:

- `GET /v1/settings`
- `PUT /v1/settings`
- `PATCH /v1/settings/translation-providers`
- `GET /v1/provider-models`
- `POST /v1/provider-models`
- `PATCH /v1/provider-models/{provider_id}`
- `DELETE /v1/provider-models/{provider_id}`
- `POST /v1/provider-models/{provider_id}/models`

Frontend:

- `frontend/src/app/(studio)/settings/page.tsx`
- Tab `Model Providers` chỉ dùng để cấu hình cloud OpenAI-compatible `base_url` như `https://ai.digipaysolution.com/v1`. UI đọc/ghi trực tiếp từ table `provider_models`, không lưu trong `data/settings.json`. UI luôn hiển thị list provider; nút `Add Provider` mở modal thêm provider, còn `Edit` và `Execute` nằm trong provider item. Modal nhập provider name/base URL/API key và lưu bằng nút `Save`. Nút `Execute` gọi backend `POST /v1/provider-models/{provider_id}/models`, backend gọi `GET {base_url}/models` và hiển thị danh sách model cloud. Provider `id` là UUID. Runtime local hiện vẫn dùng OmniVoice/Hugging Face cache trừ khi flow gọi model cloud được tích hợp.

## 19. API endpoints chính

Health/meta:

- `GET /health`
- `GET /v1/meta`
- `GET /v1/models`
- `GET /v1/languages`

Model/settings:

- `GET /v1/model-status`
- `POST /v1/model-status/install`
- `GET /v1/settings`
- `PUT /v1/settings`

Voices:

- `GET /v1/voices`
- `POST /v1/voices`
- `DELETE /v1/voices/{voice_id}`
- `POST /v1/voices/{voice_id}/rename`

Audio:

- `POST /v1/audio/speech`
- `POST /v1/audio/speech/clone`
- `POST /v1/audio/speech/design`
- `POST /v1/audio/speech/emotion-script`
- `POST /v1/audio/transcriptions`

Translation/subtitles:

- `GET /v1/translation/providers`
- `POST /v1/translation/translate`
- `POST /v1/subtitles/import`
- `POST /v1/subtitles/export`

Dubbing/diarization/dictation:

- `POST /v1/dubbing/dub`
- `POST /v1/dubbing/dub-upload`
- `GET /v1/diarization/status`
- `POST /v1/diarization/diarize`
- `POST /v1/diarization/merge`
- `GET /v1/dictation/status`
- `WS /v1/dictation/ws`

Jobs/files/history:

- `GET /v1/jobs`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/cancel`
- `DELETE /v1/jobs/{job_id}`
- `GET /v1/files?path=...`
- `GET /v1/generation-history`

## 20. CLI commands chính

```bash
uv run backend speaker-id ...
uv run backend ref-audio ...
uv run backend voice-design ...
uv run backend emotion-script ...
uv run backend transcribe ...
uv run backend subtitle-import ...
uv run backend subtitle-export ...
uv run backend translate ...
uv run backend dub ...
uv run backend diarize ...
```

Legacy scripts vẫn có:

```bash
python -m backend.scripts.build_speaker_prompt ...
python -m backend.scripts.clone_tts ...
python -m backend.scripts.clone_tts_with_speaker_id ...
python -m backend.scripts.backup_model ...
python -m backend.scripts.verify_checksum ...
```

## 21. Frontend state và value/label contract

Nguyên tắc quan trọng khi sửa UI:

- Label tiếng Việt chỉ để hiển thị.
- Value gửi backend phải giữ đúng id kỹ thuật.
- Instruct dropdown:
  - `MenuItem value={item}`
  - Text hiển thị: `instructLabel(item)`
  - Backend nhận `instruct_items: string[]`
- Emotion tag picker:
  - Hiển thị `tag.label` tiếng Việt.
  - Chèn `tag.id` vào script, ví dụ `[whisper]`.
  - Backend parse tag tiếng Anh qua `DEFAULT_TAG_ALIASES`.
- Voice dropdown:
  - `value={voice.id}`
  - Text hiển thị `voice.name || voice.id`

Nếu đổi label, không được đổi id/value trừ khi backend mapping cũng được cập nhật.

## 22. Kiểm tra sau khi sửa

Backend syntax:

```bash
```

CLI smoke:

```bash
uv run python -m backend.cli --help
uv run python -m backend.cli emotion-script --help
```

Frontend build:

```bash
cd frontend
pnpm build
```

Dev server:

```bash
cd frontend
pnpm dev
```

Nếu `pnpm build` báo lỗi ENOENT trong `.next` sau khi dev server đang chạy, dừng dev server, xóa artifact build rồi build lại:

```powershell
Remove-Item -LiteralPath .next -Recurse -Force
pnpm build
```

## 23. Trạng thái tính năng

Đã có hoặc hầu hết đã có:

- Backend core extraction.
- CLI core integration.
- Voice profiles v1.
- OpenAI-compatible speech API.
- Model status/install.
- Generation history.
- Audio DSP presets.
- Settings.
- ASR transcription.
- OpenAI-compatible transcription endpoint.
- Translation provider registry.
- Subtitle import/export.
- Video dubbing v1.
- Speaker diarization v1.
- Realtime dictation v1.
- Batch queue v1.
- Emotion script TTS v1.
- Voice Gallery v1.
- Logs/diagnostics UI/API.

Đang còn hạn chế hoặc pending:

- MCP server.
- Marketplace/import/export voice package.
- Desktop packaging.
- Fine-grained progress/cancel cho inference đang chạy.
- Silence detection cho realtime dictation.
- Emotion script mới là mapping tag -> instruct, chưa phải emotion-control native.

## 24. Khi bắt đầu session mới nên làm gì

1. Đọc file này.
2. Đọc `README.md` để nắm cách chạy.
3. Đọc `docs/refactor-feature-plan.md` để xem status phase.
4. Với frontend, đọc `StudioContext.tsx` trước page cụ thể vì context chứa action gọi API.
5. Với backend, đọc `backend/api.py` endpoint trước, sau đó đi vào module feature tương ứng.
6. Khi sửa label UI, kiểm tra value contract ở mục 21.
7. Chạy smoke/build phù hợp trước khi chốt.
