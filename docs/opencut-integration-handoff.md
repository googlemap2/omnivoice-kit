# OpenCut v0.3.0 integration handoff

Tài liệu này mô tả trạng thái `video-editor/` hiện tại và cách tích hợp OmniVoice backend vào OpenCut editor. Mục tiêu là để agent/developer lần sau đọc xong có thể bắt tay vào làm ngay, không nhầm lại giữa các repo OpenCut.

Ngày cập nhật: 2026-06-06.

## 1. Quyết định hiện tại

- `video-editor/` đang dùng upstream `https://github.com/OpenCut-app/OpenCut`.
- Version đã pin: tag `v0.3.0`.
- Commit tag đã clone: `f4bd689f51cf12a4dd0a32f602f761be314d9686`.
- Đây là base video editor chính của project hiện tại.
- Không dùng repo rewrite rỗng/latest head cho tới khi nó có timeline/editor đầy đủ.
- Không dùng lại OpenReel/custom editor cũ.
- Không tạo route config OmniVoice riêng thay thế UI editor.

Điểm quan trọng: OmniVoice phải được tích hợp vào editor flow thật của OpenCut: assets panel, properties panel, subtitles/captions, timeline/audio clips.

## 2. Trạng thái validation

Baseline đã được kiểm tra:

```powershell
cd video-editor
bun install
Copy-Item apps/web/.env.example apps/web/.env.local
bun run build:web
```

Kết quả gần nhất: `bun run build:web` pass.

Nếu build fail vì thiếu env, kiểm tra `video-editor/apps/web/.env.local`. File này có thể copy từ `video-editor/apps/web/.env.example`.

## 3. Cách chạy web editor

```powershell
cd video-editor
bun run dev:web
```

Mặc định Next.js chạy ở:

```text
http://localhost:3000
```

Các route chính:

- `/`: landing/home.
- `/projects`: danh sách project.
- `/editor/[project_id]`: editor chính.

Để test editor thủ công:

1. Mở `/projects`.
2. Tạo project mới.
3. Vào `/editor/[project_id]`.
4. Upload video ngắn.
5. Kéo video vào timeline.
6. Kiểm tra preview, timeline, properties panel.

## 4. Tech stack OpenCut v0.3.0

Root workspace:

- Package manager: Bun.
- Monorepo runner: Turbo.
- Web app: `apps/web`.
- Desktop app: `apps/desktop`, dùng GPUI/Rust, còn in-progress.
- Core/WASM/Rust: `rust/`.

Web app:

- Next.js 16.
- React 19.
- TypeScript.
- Zustand.
- Radix UI.
- Tailwind.
- OpenCut WASM package.
- Browser storage/OPFS cho media/project.

Commands chính:

```powershell
cd video-editor
bun install
bun run dev:web
bun run build:web
bun run lint:web
bun test
```

## 5. Cấu trúc source cần biết

Các file/folder quan trọng:

```text
video-editor/
  AGENTS.md
  package.json
  apps/web/package.json
  apps/web/.env.example
  apps/web/src/app/
  apps/web/src/app/editor/[project_id]/page.tsx
  apps/web/src/components/editor/
  apps/web/src/components/editor/panels/assets/
  apps/web/src/components/editor/panels/preview/
  apps/web/src/components/editor/panels/properties/
  apps/web/src/components/editor/panels/timeline/
  apps/web/src/core/
  apps/web/src/core/managers/
  apps/web/src/editor/
  apps/web/src/media/
  apps/web/src/subtitles/
  apps/web/src/timeline/
  apps/web/src/services/
```

Đọc trước khi sửa:

1. `video-editor/AGENTS.md`
2. `video-editor/README.md`
3. `video-editor/apps/web/src/app/editor/[project_id]/page.tsx`
4. `video-editor/apps/web/src/core/index.ts`
5. `video-editor/apps/web/src/editor/use-editor.ts`
6. `video-editor/apps/web/src/components/providers/editor-provider.tsx`
7. `video-editor/apps/web/src/components/editor/panels/assets/index.tsx`
8. `video-editor/apps/web/src/components/editor/panels/properties/index.tsx`
9. `video-editor/apps/web/src/components/editor/panels/timeline/`
10. `video-editor/apps/web/src/subtitles/`

## 6. Editor architecture

OpenCut editor có các khối chính:

- Assets panel: nhập media, text, subtitles, effects, graphics.
- Preview panel: canvas/player.
- Timeline panel: tracks và timeline elements.
- Properties panel: chỉnh selected element.
- Core managers: quản lý project, media, timeline, selection, history.
- Storage services: lưu media/project trong browser storage.

Quy tắc làm việc:

- UI nằm trong `apps/web`.
- Logic platform-agnostic nên ưu tiên đặt trong `rust/` theo định hướng upstream, nhưng tích hợp OmniVoice ban đầu có thể đặt trong `apps/web/src/omnivoice/` vì đây là UI/backend integration layer.
- Không duplicate logic vào nhiều panel; tách API client và helper riêng.
- Mọi thay đổi timeline phải dùng command/manager hiện có nếu có thể, không mutate state thẳng.

## 7. Điểm tích hợp OmniVoice đề xuất

Tạo folder mới:

```text
video-editor/apps/web/src/omnivoice/
  client.ts
  settings-store.ts
  transcription.ts
  tts.ts
  srt.ts
  audio.ts
  components/
    omnivoice-assets-view.tsx
    omnivoice-settings.tsx
    omnivoice-transcription-panel.tsx
    omnivoice-tts-panel.tsx
    omnivoice-audio-properties.tsx
```

Không đặt OmniVoice vào homepage. Không thay route `/`.

### 7.1 Backend URL setting

UI nên nằm trong editor, ví dụ assets panel tab `OmniVoice` hoặc settings view của editor.

State:

- `apiBaseUrl`
- `healthStatus`
- `lastMemorySnapshot`

Storage:

- localStorage key đề xuất: `omnivoice.apiBaseUrl`

Header bắt buộc khi dùng ngrok:

```http
ngrok-skip-browser-warning: true
```

### 7.2 OmniVoice API client

Endpoints cần hỗ trợ:

- `GET /health`
- `GET /v1/diagnostics/memory`
- `POST /v1/models/unload`
- `POST /v1/audio/transcriptions`
- `POST /v1/audio/speech/emotion-script`

Default values:

```ts
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TRANSCRIPTION_MODEL = "Systran/faster-whisper-large-v3";
const DEFAULT_TTS_MODEL = "kjanh/KhanhTTS-OmniVoice";
```

Transcription request:

```ts
const formData = new FormData();
formData.append("file", file);
formData.append("model", model);
formData.append("response_format", "srt");
formData.append("word_timestamps", "true");
formData.append("translate", String(translate));
formData.append("language", language);
formData.append("target_language", targetLanguage);
```

TTS request:

```json
{
  "model": "kjanh/KhanhTTS-OmniVoice",
  "input": "text",
  "voice": "yen",
  "response_format": "wav",
  "language": "vi",
  "speed": 1.2,
  "effect_preset": "raw"
}
```

Endpoint TTS cần dùng:

```text
POST /v1/audio/speech/emotion-script
```

## 8. Transcription integration

Mục tiêu: tạo caption/subtitle từ video/audio trong editor bằng OmniVoice backend.

Vị trí UI đề xuất:

- Assets panel tab `OmniVoice`.
- Section `Transcribe to captions`.

Controls:

- Chọn media input: current selected media hoặc upload/current timeline audio.
- Language: `vi`, `en`, `ja`, `ko`, `zh`.
- Translate checkbox.
- Target language nếu translate bật.
- Engine/provider: `OmniVoice backend` trước, giữ local OpenCut transcription như option riêng nếu cần.
- Response format mặc định: `srt`.

Flow:

1. Lấy file media từ existing media/storage.
2. Gọi `/v1/audio/transcriptions` với `response_format=srt`.
3. Parse SRT bằng parser hiện có trong `apps/web/src/subtitles/`.
4. Insert captions vào timeline bằng command/helper hiện có.
5. Lưu metadata để TTS có thể map caption timing.

Không nên:

- Tạo parser SRT mới nếu OpenCut đã có parser.
- Insert captions bằng cách mutate state trực tiếp.
- Làm mất local transcription flow hiện có.

## 9. TTS from captions

Mục tiêu: dùng captions/SRT timing để generate audio clips và map đúng timeline.

UI đề xuất:

- Trong section `Transcribe to captions`, đặt checkbox `Map TTS to timeline by caption timing`.
- Khi checkbox bật mới show:
  - TTS model.
  - Voice.
  - Language.
  - Speed.
  - Effect preset.

Flow:

1. User generate captions.
2. Nếu map TTS bật, lấy từng caption segment.
3. Gọi `/v1/audio/speech/emotion-script` cho từng segment.
4. Lưu WAV blob vào storage/media store.
5. Tạo audio timeline element tại caption start time.
6. Duration audio đo từ metadata thực tế.
7. Gắn metadata OmniVoice vào audio element:
   - source caption id/index.
   - text.
   - model.
   - voice.
   - language.
   - speed.
   - effect preset.

Batch policy:

- Generate tuần tự hoặc concurrency thấp để tránh RAM Colab tăng mạnh.
- Có progress UI.
- Có cancel.
- Sau batch có thể gọi `/v1/diagnostics/memory`.
- Nếu backend đang `VOICEKIT_KEEP_MODELS_LOADED=false`, chấp nhận mỗi request load/release model.

## 10. Regenerate selected TTS audio

Mục tiêu: chọn audio clip đã được OmniVoice generate, mở properties/OmniVoice tab, chỉnh text/model/voice/effect rồi regenerate.

Vị trí UI đề xuất:

- Properties panel khi selected element là audio clip có metadata OmniVoice.
- Sub tab hoặc section `OmniVoice TTS`.

Yêu cầu bắt buộc:

- Khi click audio clip, text phải được fill vào field `Transcript / TTS text`.
- Replace phải hoạt động với mọi audio clip, không chỉ clip đầu tiên.
- Sau replace, metadata của clip phải cập nhật theo audio mới.
- Có preview audio trước khi replace.
- Không cắt sai duration; sau replace phải đo lại duration blob mới.

Flow:

1. Detect selected audio element.
2. Load `metadata.omnivoice`.
3. Fill UI.
4. Generate new WAV blob.
5. Preview blob bằng `<audio controls>`.
6. Khi user xác nhận replace:
   - lưu blob mới vào storage.
   - update media reference.
   - update timeline element duration nếu cần.
   - update metadata.
   - giữ start time/track/index của clip cũ.

## 11. Caption position apply all

Nếu cần chỉnh position cho tất cả captions:

- UI nên có `Apply to all captions`.
- Chỉ áp dụng cho caption/text elements thuộc cùng generated caption group nếu có metadata group id.
- Không apply bừa sang text overlay thường.

Metadata đề xuất:

```ts
type OmniVoiceCaptionMetadata = {
  provider: "omnivoice";
  groupId: string;
  segmentIndex: number;
  sourceMediaId?: string;
};
```

## 12. Memory/Colab diagnostics

UI OmniVoice nên có section nhỏ:

- `Check backend`
- `Memory`
- `Unload all models`
- `Unload TTS`
- `Unload Emotion TTS`

API:

```text
GET /v1/diagnostics/memory
POST /v1/models/unload
```

Request unload theo feature:

```json
{ "feature": "emotion_tts" }
```

Không tự động cache model dài hạn trên Colab nếu mục tiêu là tiết kiệm RAM. Tôn trọng policy backend:

- `VOICEKIT_KEEP_MODELS_LOADED`
- `VOICEKIT_CACHE_TTS`
- `VOICEKIT_CACHE_EMOTION_TTS`

## 13. Known pitfalls

### 13.1 Không nhầm repo

- `OpenCut-app/OpenCut` latest head từng có giai đoạn rewrite rất mỏng.
- Project hiện pin tag `v0.3.0` vì tag này có editor/timeline thực tế.
- Không ghi docs rằng route `/` có OmniVoice config page.

### 13.2 Encoding tiếng Việt

- File docs/source phải giữ UTF-8.
- Không dùng PowerShell command kiểu here-string không kiểm soát encoding để rewrite text tiếng Việt.
- Nếu cần script sửa docs, dùng `apply_patch` hoặc tool/editor đảm bảo UTF-8.

### 13.3 Browser storage quota

Generated TTS files lưu browser storage/OPFS có thể vượt quota. Cần handle lỗi quota và cho user xóa media/generated audio.

### 13.4 Media duration

Sau khi TTS trả WAV, phải đo duration thực tế trước khi insert/replace timeline clip.

### 13.5 Timeline time unit

Không mix seconds và internal timeline/media time. Luôn kiểm tra helper hiện có trong `apps/web/src/timeline/` hoặc `apps/web/src/media/`.

### 13.6 Không phá local features

OpenCut đã có transcription/import/export riêng. OmniVoice nên là backend provider bổ sung, không replace toàn bộ flow nếu không cần.

## 14. Implementation phases

### Phase 0: Baseline

Đã hoàn thành.

Acceptance:

- `video-editor/` là OpenCut tag `v0.3.0`.
- `bun install` pass.
- `bun run build:web` pass.
- `/projects` và `/editor/[project_id]` chạy được trong dev.

### Phase 1: OmniVoice settings tab

Files dự kiến:

- `apps/web/src/omnivoice/client.ts`
- `apps/web/src/omnivoice/settings-store.ts`
- `apps/web/src/omnivoice/components/omnivoice-settings.tsx`
- assets panel tab/store hiện có.

Acceptance:

- Có tab/tool `OmniVoice` trong editor.
- User set backend URL.
- URL lưu localStorage.
- Health check gọi `/health`.
- Có ngrok bypass header.

### Phase 2: Transcribe to captions

Files dự kiến:

- `apps/web/src/omnivoice/transcription.ts`
- `apps/web/src/omnivoice/components/omnivoice-transcription-panel.tsx`
- subtitle parser/insert helpers hiện có.

Acceptance:

- Chọn media/current timeline audio.
- Gọi backend transcription response `srt`.
- Parse SRT.
- Insert captions vào timeline.
- Không phá local transcription/import subtitles.

### Phase 3: Map TTS to timeline by caption timing

Files dự kiến:

- `apps/web/src/omnivoice/tts.ts`
- `apps/web/src/omnivoice/audio.ts`
- `apps/web/src/omnivoice/components/omnivoice-tts-panel.tsx`

Acceptance:

- Checkbox nằm trong `Transcribe to captions`.
- Khi checked mới show model/voice/effect/speed.
- Generate audio clip theo từng caption.
- Insert audio đúng start time.
- Metadata được lưu đủ để regenerate.

### Phase 4: Regenerate selected TTS audio

Files dự kiến:

- properties panel registry hiện có.
- `apps/web/src/omnivoice/components/omnivoice-audio-properties.tsx`

Acceptance:

- Chọn audio clip đã generate thì thấy OmniVoice properties.
- Text/model/voice/effect được fill từ metadata.
- Generate preview audio.
- Replace đúng selected clip thứ nhất, thứ hai, hoặc bất kỳ clip nào.
- Metadata và duration cập nhật theo audio mới.

### Phase 5: Diagnostics and polish

Acceptance:

- Progress/cancel batch TTS.
- Error detail rõ ràng.
- Memory diagnostics.
- Model unload buttons.
- Empty states và loading states rõ.

## 15. Baseline checklist trước khi sửa code

Trước mỗi phase:

```powershell
cd video-editor
if (-not (Test-Path apps/web/.env.local)) { Copy-Item apps/web/.env.example apps/web/.env.local }
bun install
bun run build:web
```

Manual smoke:

1. Mở `/projects`.
2. Tạo project.
3. Vào editor.
4. Upload video.
5. Kéo vào timeline.
6. Play preview.
7. Add/import subtitle nếu phase liên quan captions.
8. Kiểm tra console không có runtime error nghiêm trọng.

## 16. Next action

Bước tiếp theo nên làm: Phase 1, tạo OmniVoice tab/tool trong editor assets panel hoặc settings panel. Không thêm homepage config.
