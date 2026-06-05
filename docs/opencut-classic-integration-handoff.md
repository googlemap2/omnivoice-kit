# OpenCut Classic integration handoff

Tài liệu này dùng để agent/developer lần sau có thể đọc nhanh, hiểu kiến trúc `opencut-app/opencut-classic`, và bắt tay vào tích hợp OmniVoice backend mà không phải audit lại từ đầu.

Ngày audit: 2026-06-06.

Nguồn audit:

- Upstream: `https://github.com/opencut-app/opencut-classic`
- Trạng thái upstream theo README: legacy/original codebase, archived/no longer maintained; rewrite mới ở `opencut-app/opencut`.
- License: MIT.

Nếu cần inspect source lại:

```powershell
if (-not (Test-Path external)) { New-Item -ItemType Directory external | Out-Null }
git clone --depth 1 https://github.com/opencut-app/opencut-classic.git external/opencut-classic
```

## 1. Kết luận kỹ thuật

`opencut-classic` là lựa chọn phù hợp hơn `opencut-app/opencut` hiện tại nếu mục tiêu ngắn hạn là có video editor web đầy đủ để tích hợp OmniVoice vào timeline.

Lý do:

- `opencut-app/opencut` hiện là rewrite mới, app web còn rất mỏng. Trong repo này, route `/` của `video-editor` đã có OmniVoice backend test panel, nhưng chưa có timeline editor.
- `opencut-classic` đã có editor thực tế:
  - Media import.
  - Timeline nhiều track.
  - Audio/video/image/text element.
  - Caption generation/import.
  - Properties panel.
  - Export MP4/WebM.
  - Browser storage project/media.
- Stack vẫn hợp hướng hiện tại: TypeScript, React, Next.js, Bun, web editor.
- License MIT ít ràng buộc hơn OpenShot/Shotcut GPL.

Rủi ro:

- Upstream classic đã archived/no longer maintained.
- Có nhiều business logic còn ở TypeScript, dù AGENTS.md upstream nói đang migrate logic sang Rust.
- Desktop app `apps/desktop` dùng GPUI/Rust và còn in progress; không phải Tauri.
- Transcription mặc định chạy local browser worker bằng `@huggingface/transformers`, không dùng OmniVoice backend.
- Export chạy browser renderer, không phải server-side FFmpeg pipeline.

Khuyến nghị:

1. Nếu cần editor usable ngay: dùng `opencut-classic` làm base thay cho `video-editor`.
2. Nếu cần Tauri desktop shell: wrap web app bằng Tauri riêng hoặc chờ/đổi hướng; classic desktop không phải Tauri.
3. Tích hợp OmniVoice theo từng feature nhỏ:
   - Backend URL setting.
   - Captions dùng `/v1/audio/transcriptions`.
   - TTS map SRT/caption timing thành audio track.
   - Audio clip regenerate bằng `/v1/audio/speech/emotion-script`.

## 2. Setup local

### 2.1 Prerequisites

- Bun. Upstream `package.json` khai báo `bun@1.2.18`.
- Docker + Docker Compose nếu muốn chạy DB/Redis local đầy đủ.
- Rust chỉ cần nếu chỉnh WASM hoặc desktop.

### 2.2 Commands

Từ root repo OmniVoice:

```powershell
cd external/opencut-classic
Copy-Item apps/web/.env.example apps/web/.env.local
docker compose up -d db redis serverless-redis-http
bun install
bun dev:web
```

Web chạy mặc định ở:

```text
http://localhost:3000
```

Build web:

```powershell
cd external/opencut-classic
bun run build:web
```

Test:

```powershell
cd external/opencut-classic
bun test
```

Lint:

```powershell
cd external/opencut-classic
bun run lint:web
```

### 2.3 Environment

File mẫu: `external/opencut-classic/apps/web/.env.example`.

Các env chính:

```env
NODE_ENV=development
NEXT_PUBLIC_SITE_URL=http://localhost:3000
DATABASE_URL="postgresql://opencut:opencut@localhost:5432/opencut"
BETTER_AUTH_SECRET=your_better_auth_secret
UPSTASH_REDIS_REST_URL=http://localhost:8079
UPSTASH_REDIS_REST_TOKEN=example_token
FREESOUND_CLIENT_ID=your_client_id_here
FREESOUND_API_KEY=your_api_key_here
```

Env cần thêm cho OmniVoice:

```env
NEXT_PUBLIC_OMNIVOICE_API_BASE_URL=http://127.0.0.1:8000
```

Nếu dùng ngrok/Colab:

```env
NEXT_PUBLIC_OMNIVOICE_API_BASE_URL=https://your-ngrok-url.ngrok-free.dev
```

Client request tới ngrok nên thêm header:

```http
ngrok-skip-browser-warning: true
```

## 3. Repo structure

Root:

```text
external/opencut-classic/
  apps/
    web/          Next.js web editor.
    desktop/      Native GPUI desktop app, in progress.
  rust/
    crates/       Platform-agnostic Rust core pieces.
    wasm/         WASM bindings used by web.
  docs/           Upstream architecture docs.
  docker-compose.yml
  package.json
  Cargo.toml
```

Web app:

```text
apps/web/src/
  app/                    Next.js App Router pages/routes.
  components/editor/      Editor shell panels/header/onboarding.
  core/                   EditorCore and managers.
  timeline/               Timeline data model, components, placement, drag/drop.
  commands/               Undoable command system.
  media/                  Import, processing, audio decode/mix, thumbnails.
  subtitles/              SRT/ASS parse + caption insertion.
  transcription/          Caption chunking/types/local model metadata.
  services/transcription/ Browser worker transcription service.
  services/storage/       IndexedDB + OPFS persistence.
  services/renderer/      Canvas/WebGPU/WASM renderer/export.
  project/                Project types and UI.
  export/                 Export options/result/download helpers.
```

## 4. Application shell

Editor route:

- `external/opencut-classic/apps/web/src/app/editor/[project_id]/page.tsx`

Flow:

1. Reads `project_id` from route.
2. Wraps UI in `EditorProvider`.
3. Layout:
   - Left: `AssetsPanel`
   - Center: `PreviewPanel`
   - Right: `PropertiesPanel`
   - Bottom: `Timeline`

Important components:

- `components/editor/editor-header.tsx`
- `components/editor/panels/assets/index.tsx`
- `components/editor/panels/properties/index.tsx`
- `timeline/components/index.tsx`
- `preview/components/*`

## 5. Core state architecture

Central class:

- `external/opencut-classic/apps/web/src/core/index.ts`

`EditorCore` singleton owns managers:

```ts
EditorCore
  command: CommandManager
  timeline: TimelineManager
  playback: PlaybackManager
  scenes: ScenesManager
  project: ProjectManager
  media: MediaManager
  renderer: RendererManager
  save: SaveManager
  audio: AudioManager
  selection: SelectionManager
  clipboard: ClipboardManager
  diagnostics: DiagnosticsManager
```

Usage from React:

- Hook: `external/opencut-classic/apps/web/src/editor/use-editor.ts`
- Provider: `external/opencut-classic/apps/web/src/components/providers/editor-provider.tsx`

Pattern:

- React components read manager state via `useEditor(selector)`.
- Mutations should go through manager methods or commands, not direct object mutation.
- Timeline changes should use `editor.timeline.*`.
- Undoable edits use `CommandManager` via existing commands.

## 6. Timeline model

Main type file:

- `external/opencut-classic/apps/web/src/timeline/types.ts`

Track types:

```ts
type TrackType = "video" | "text" | "audio" | "graphic" | "effect";
```

Scene tracks:

```ts
interface SceneTracks {
  overlay: OverlayTrack[];
  main: VideoTrack;
  audio: AudioTrack[];
}
```

Element types:

```ts
TimelineElement =
  | AudioElement
  | VideoElement
  | ImageElement
  | TextElement
  | StickerElement
  | GraphicElement
  | EffectElement;
```

Audio element:

```ts
UploadAudioElement {
  type: "audio";
  sourceType: "upload";
  mediaId: string;
  startTime: MediaTime;
  duration: MediaTime;
  trimStart: MediaTime;
  trimEnd: MediaTime;
  retime?: { rate: number; maintainPitch?: boolean };
}
```

Video element:

```ts
VideoElement {
  type: "video";
  mediaId: string;
  isSourceAudioEnabled?: boolean;
  retime?: RetimeConfig;
}
```

Text/caption element:

```ts
TextElement {
  type: "text";
  params.content: string;
  params["transform.positionX"]: number;
  params["transform.positionY"]: number;
}
```

Time type:

- Uses `MediaTime` from `apps/web/src/wasm/media-time.ts`.
- Conversion helpers:
  - `mediaTimeFromSeconds({ seconds })`
  - `mediaTimeToSeconds({ time })`
  - `TICKS_PER_SECOND`

Never store raw seconds in timeline elements. Convert to `MediaTime`.

## 7. Timeline mutation

Manager:

- `external/opencut-classic/apps/web/src/core/managers/timeline-manager.ts`

Common methods:

```ts
editor.timeline.addTrack({ type, index });
editor.timeline.insertElement({ element, placement });
editor.timeline.updateElements({ updates, pushHistory });
editor.timeline.deleteElements({ elements });
editor.timeline.splitElements({ elements, splitTime });
editor.timeline.moveElements({ moves, createTracks });
editor.timeline.getTotalDuration();
editor.timeline.getElementsWithTracks({ elements });
```

Insert command:

- `external/opencut-classic/apps/web/src/commands/timeline/element/insert-element.ts`

Insert pattern:

```ts
editor.timeline.insertElement({
  element,
  placement: { mode: "auto", trackType: "audio" },
});
```

or explicit track:

```ts
editor.timeline.insertElement({
  element,
  placement: { mode: "explicit", trackId },
});
```

For inserting many captions/audio clips, prefer `BatchCommand` with `AddTrackCommand` + many `InsertElementCommand`, same as subtitles implementation.

## 8. Media import and storage

Media manager:

- `external/opencut-classic/apps/web/src/core/managers/media-manager.ts`

Media asset type:

- `external/opencut-classic/apps/web/src/media/types.ts`

```ts
interface MediaAsset {
  id: string;
  name: string;
  type: "image" | "video" | "audio";
  file: File;
  url?: string;
  thumbnailUrl?: string;
  duration?: number;
  width?: number;
  height?: number;
  fps?: number;
  hasAudio?: boolean;
  ephemeral?: boolean;
}
```

Processing:

- `external/opencut-classic/apps/web/src/media/processing.ts`
- `processMediaAssets({ files })`:
  - validates type.
  - checks browser storage quota.
  - creates object URL.
  - extracts video duration/dimensions/fps/thumbnail via Mediabunny.
  - extracts audio duration via browser media element.

Storage:

- `external/opencut-classic/apps/web/src/services/storage/service.ts`
- Project metadata is stored in IndexedDB.
- Media files are stored in OPFS.
- Media metadata is stored in IndexedDB per project.

Add media:

```ts
await editor.media.addMediaAsset({
  projectId,
  asset,
});
```

Important: generated OmniVoice audio should be converted to a browser `File` and added through `editor.media.addMediaAsset()`, not only inserted as a timeline element. Otherwise persistence/export/audio playback will break.

## 9. Assets panel

Store:

- `external/opencut-classic/apps/web/src/components/editor/panels/assets/assets-panel-store.tsx`

Current tabs:

```ts
media
sounds
text
stickers
effects
transitions
captions
adjustment
settings
```

Tab UI:

- `external/opencut-classic/apps/web/src/components/editor/panels/assets/tabbar.tsx`

Panel switch:

- `external/opencut-classic/apps/web/src/components/editor/panels/assets/index.tsx`

To add an OmniVoice tab:

1. Add key to `TAB_KEYS`, for example `omnivoice`.
2. Add icon/label to `tabs`.
3. Add view in `AssetsPanel.viewMap`.
4. Implement `components/editor/panels/assets/views/omnivoice.tsx` or `omnivoice/components/assets-view.tsx`.

Recommended: put global OmniVoice tools in left AssetsPanel, not PropertiesPanel:

- Backend settings.
- Transcribe current timeline.
- Import SRT.
- Generate TTS from captions.
- Batch TTS controls.

## 10. Properties panel

Panel:

- `external/opencut-classic/apps/web/src/components/editor/panels/properties/index.tsx`

Registry:

- `external/opencut-classic/apps/web/src/components/editor/panels/properties/registry.tsx`

Current behavior:

- If no selection: empty view.
- If multiple selections: simple message.
- If one element selected: loads config by element type.

Audio element config currently:

```ts
tabs: [buildAudioTab({ element }), buildSpeedTab({ element })]
```

To add "OmniVoice" tab for selected audio:

1. Create `OmnivoiceAudioTab`.
2. Add `buildOmnivoiceAudioTab({ element })`.
3. Add to `getAudioConfig()` tabs.
4. Use selected audio element + media asset to prefill transcript/TTS text if metadata exists.

Use this for clip-level operations:

- Regenerate selected TTS audio.
- Preview regenerated audio.
- Replace selected audio asset/element.
- Speed/retime generated audio.

Do not put project-wide transcript generation here.

## 11. Captions and transcription

Assets tab:

- `external/opencut-classic/apps/web/src/subtitles/components/assets-view.tsx`

Current flow:

1. `extractTimelineAudio()` from current timeline.
2. `decodeAudioToFloat32()` to 16 kHz float32.
3. `transcriptionService.transcribe()` uses browser worker.
4. `buildCaptionChunks()` splits segments into caption chunks.
5. `insertCaptionChunksAsTextTrack()` inserts text track.

Local browser transcription service:

- `external/opencut-classic/apps/web/src/services/transcription/service.ts`
- Worker:
  - `external/opencut-classic/apps/web/src/services/transcription/worker.ts`
- Model metadata:
  - `external/opencut-classic/apps/web/src/transcription/models.ts`
  - `external/opencut-classic/apps/web/src/transcription/languages.ts`
  - `external/opencut-classic/apps/web/src/transcription/supported-languages.ts`

Caption chunking:

- `external/opencut-classic/apps/web/src/transcription/caption.ts`

Subtitle import:

- `external/opencut-classic/apps/web/src/subtitles/parse.ts`
- `external/opencut-classic/apps/web/src/subtitles/srt.ts`
- `external/opencut-classic/apps/web/src/subtitles/ass.ts`

Caption insertion:

- `external/opencut-classic/apps/web/src/subtitles/insert.ts`

```ts
insertCaptionChunksAsTextTrack({ editor, captions });
```

Caption element builder:

- `external/opencut-classic/apps/web/src/subtitles/build-subtitle-text-element.ts`

This sets:

- text content.
- font family/size/color.
- text alignment.
- bottom/middle/top placement.
- `transform.positionX/Y`.
- `startTime` and `duration`.

## 12. OmniVoice backend integration design

### 12.1 Add OmniVoice API client

Create:

```text
apps/web/src/omnivoice/client.ts
apps/web/src/omnivoice/types.ts
apps/web/src/omnivoice/srt.ts
apps/web/src/omnivoice/audio.ts
```

Suggested client helpers:

```ts
export function getOmniVoiceBaseUrl(): string;
export async function transcribeWithOmniVoice(args): Promise<CaptionChunk[]>;
export async function generateOmniVoiceSpeech(args): Promise<Blob>;
export async function getOmniVoiceHealth(): Promise<boolean>;
```

Base URL priority:

1. localStorage setting, e.g. `omnivoice.apiBaseUrl`.
2. env `NEXT_PUBLIC_OMNIVOICE_API_BASE_URL`.
3. fallback `http://127.0.0.1:8000`.

Headers:

```ts
{
  "ngrok-skip-browser-warning": "true"
}
```

### 12.2 Transcribe current timeline with OmniVoice

Replace or add option in:

- `external/opencut-classic/apps/web/src/subtitles/components/assets-view.tsx`

Recommended UX:

- Keep existing local transcription as "Browser".
- Add engine select:
  - `Browser local`
  - `OmniVoice backend`
- Add language select.
- Add optional translate target language.
- Add response format internal as `srt` or `verbose_json`.

Backend endpoint:

```http
POST /v1/audio/transcriptions
Content-Type: multipart/form-data
```

Typical form fields:

```text
file=<audio wav/blob>
model=Systran/faster-whisper-large-v3
response_format=srt
word_timestamps=true
translate=false
target_language=en
```

Implementation approach:

1. Keep `extractTimelineAudio()` to produce a timeline audio blob.
2. Send that blob to OmniVoice endpoint.
3. If response is SRT:
   - parse through existing `parseSubtitleFile({ fileName: "omnivoice.srt", input })`.
   - call `insertCaptionChunksAsTextTrack({ editor, captions })`.
4. If response is verbose JSON:
   - convert segments to `CaptionChunk[]`.
   - call `insertCaptionChunksAsTextTrack`.

Why SRT is good:

- User requested SRT previously.
- OpenCut already has robust SRT parser/import path.
- Less coupling to backend JSON details.

### 12.3 Generate TTS mapped by caption timing

Goal:

- For each caption/text cue, call OmniVoice TTS and insert generated audio clip at caption start time.
- Each generated audio clip should be added as media asset and inserted as audio element.

Recommended source of captions:

- Selected text track elements named `Caption N`.
- Or all text elements in a selected text track.
- Or parse latest SRT generated in the OmniVoice panel.

Backend endpoint:

```http
POST /v1/audio/speech/emotion-script
Content-Type: application/json
```

Body:

```json
{
  "model": "kjanh/KhanhTTS-OmniVoice",
  "input": "caption text",
  "voice": "yen",
  "response_format": "wav",
  "language": "vi",
  "speed": 1.0,
  "effect_preset": "raw"
}
```

Implementation steps:

1. Collect captions:
   - text content from `TextElement.params.content`.
   - start time from `TextElement.startTime`.
   - duration from `TextElement.duration`.
2. For each caption:
   - call TTS.
   - get WAV blob.
   - create `File`:

```ts
const file = new File([blob], `omnivoice-caption-${index + 1}.wav`, {
  type: "audio/wav",
  lastModified: Date.now(),
});
```

3. Add media asset:

```ts
const asset = await editor.media.addMediaAsset({
  projectId,
  asset: {
    name: file.name,
    type: "audio",
    file,
    url: URL.createObjectURL(file),
    duration: measuredDurationSeconds,
  },
});
```

4. Insert audio element:

```ts
editor.timeline.insertElement({
  element: {
    type: "audio",
    sourceType: "upload",
    mediaId: asset.id,
    name: asset.name,
    startTime: caption.startTime,
    duration: mediaTimeFromSeconds({ seconds: measuredDurationSeconds }),
    trimStart: ZERO_MEDIA_TIME,
    trimEnd: ZERO_MEDIA_TIME,
    params: {
      ...DEFAULTS.audio.element.params,
    },
  },
  placement: { mode: "auto", trackType: "audio" },
});
```

Use actual defaults from `timeline/defaults.ts`; verify key shape before implementation.

5. If generated audio duration differs from caption duration:
   - Option A: keep audio natural duration.
   - Option B: set retime rate to match caption duration.
   - Option C: expose a setting:
     - `Keep natural duration`
     - `Fit to caption duration`

Recommended default: keep natural duration. Add fit option later.

### 12.4 Regenerate selected audio clip

Location:

- Properties panel audio config.

Files:

- `components/editor/panels/properties/registry.tsx`
- new `components/editor/panels/properties/components/omnivoice-audio-tab.tsx`

Flow:

1. User selects one audio element.
2. Properties panel shows OmniVoice tab.
3. Prefill text:
   - Need store generated TTS metadata.
   - Current `MediaAssetData` has no custom metadata.
   - Add minimal metadata field or keep a separate IndexedDB/localStorage mapping.

Recommended metadata approach:

Add optional field to `MediaAssetData`:

```ts
omnivoice?: {
  kind: "tts";
  text: string;
  model: string;
  voice: string;
  language: string;
  effectPreset: string;
  sourceCaptionElementId?: string;
};
```

Then update:

- `services/storage/types.ts`
- `services/storage/service.ts` save/load media metadata.
- storage migrations if project schema requires it.

Replace flow:

1. Generate new blob with current tab settings.
2. Preview blob in `<audio controls>`.
3. On "Replace":
   - Add new media asset or update existing asset.
   - Safer: add new asset and patch timeline element `mediaId`.
   - Use `editor.timeline.updateElements()`.
   - Update element duration/trim based on new audio.
4. Remove old generated asset optionally only if not used elsewhere.

Avoid mutating OPFS file directly unless storage adapter has update semantics fully understood.

## 13. Backend API contract needed

Backend currently relevant endpoints:

```http
GET /health
GET /v1/diagnostics/memory
POST /v1/models/unload
POST /v1/audio/transcriptions
POST /v1/audio/speech/emotion-script
```

Frontend should not hardcode one ngrok URL.

Required FE settings:

- API base URL.
- Model for ASR.
- Transcription language.
- Translate enabled.
- Target language.
- TTS model.
- TTS voice.
- TTS language.
- TTS speed.
- TTS effect preset.
- Cache policy info optional read-only from diagnostics.

## 14. Recommended implementation phases

### Phase 0: Decide base replacement

If choosing classic:

1. Remove current `video-editor/`.
2. Copy/clone `opencut-classic` into `video-editor/`.
3. Remove nested `.git`.
4. Update root docs to say `video-editor` is OpenCut Classic.
5. Run:

```powershell
cd video-editor
bun install
bun run build:web
```

Do not integrate OmniVoice before baseline build passes.

### Phase 1: OmniVoice settings panel

Files:

- `apps/web/src/omnivoice/client.ts`
- `apps/web/src/omnivoice/settings-store.ts`
- `apps/web/src/components/editor/panels/assets/assets-panel-store.tsx`
- `apps/web/src/components/editor/panels/assets/index.tsx`
- new `apps/web/src/omnivoice/components/assets-view.tsx`

Acceptance:

- New left tab "OmniVoice".
- User can set backend URL.
- URL persists in localStorage.
- Health check calls `/health` with ngrok bypass header.

### Phase 2: OmniVoice transcription

Files:

- `apps/web/src/omnivoice/transcription.ts`
- `apps/web/src/subtitles/components/assets-view.tsx` or OmniVoice tab.

Acceptance:

- User can transcribe current timeline audio using backend.
- Captions inserted as text track.
- SRT response parsed using existing subtitle parser.

### Phase 3: TTS from captions

Files:

- `apps/web/src/omnivoice/tts.ts`
- `apps/web/src/omnivoice/audio.ts`
- `apps/web/src/omnivoice/components/assets-view.tsx`

Acceptance:

- Select all caption text elements or use last generated captions.
- Generate one audio clip per caption.
- Insert audio clips aligned to caption start time.
- Generated clips persist after reload.

### Phase 4: Regenerate selected audio

Files:

- `apps/web/src/components/editor/panels/properties/registry.tsx`
- new `apps/web/src/omnivoice/components/properties-audio-tab.tsx`
- storage metadata updates.

Acceptance:

- Selecting generated audio shows OmniVoice tab.
- Text/model/voice/effect are prefilled.
- Regenerate creates preview.
- Replace updates correct selected audio clip, including clips after the first.

### Phase 5: Polish and diagnostics

Acceptance:

- Progress UI for batch TTS.
- Cancel in-flight generation.
- Errors show backend status/detail.
- Memory diagnostics surfaced for Colab.
- `/v1/models/unload` button available.

## 15. Known pitfalls

### 15.1 Browser storage quota

Generated TTS files are stored in OPFS. Large batch generation can exceed browser quota. Always call existing storage capacity checks or handle `StorageQuotaExceededError`.

### 15.2 Media duration measurement

After TTS returns WAV, measure duration before inserting timeline element. Use browser audio metadata or existing media processing path.

### 15.3 Timeline time unit

Never mix seconds and `MediaTime`. Use `mediaTimeFromSeconds`.

### 15.4 Caption timing drift

If generated TTS audio is longer than caption duration, later clips may overlap. Decide per UX:

- Allow overlaps on separate audio tracks.
- Fit audio duration to caption duration via retime.
- Generate with speed adjusted.

### 15.5 Undo/redo

Direct manager mutation may bypass undo. Prefer `BatchCommand`, `InsertElementCommand`, `UpdateElementsCommand`.

### 15.6 Multiple selected elements

Properties panel currently handles multiple selection by showing a simple message. Clip-level OmniVoice actions should start with single selected audio clip only.

### 15.7 Local browser ASR vs backend ASR

Existing `transcriptionService` loads Whisper-like model in browser worker and may consume client RAM. For Colab/backend workflow, OmniVoice backend should be default or clearly selectable.

### 15.8 Desktop expectation

Classic desktop is GPUI/Rust in progress. If product requires Tauri, this repo does not satisfy that out of the box.

## 16. File map for agents

Read in this order before coding:

1. `external/opencut-classic/AGENTS.md`
2. `external/opencut-classic/README.md`
3. `external/opencut-classic/package.json`
4. `external/opencut-classic/apps/web/package.json`
5. `external/opencut-classic/apps/web/src/app/editor/[project_id]/page.tsx`
6. `external/opencut-classic/apps/web/src/core/index.ts`
7. `external/opencut-classic/apps/web/src/core/managers/timeline-manager.ts`
8. `external/opencut-classic/apps/web/src/core/managers/media-manager.ts`
9. `external/opencut-classic/apps/web/src/timeline/types.ts`
10. `external/opencut-classic/apps/web/src/commands/timeline/element/insert-element.ts`
11. `external/opencut-classic/apps/web/src/components/editor/panels/assets/assets-panel-store.tsx`
12. `external/opencut-classic/apps/web/src/components/editor/panels/assets/index.tsx`
13. `external/opencut-classic/apps/web/src/subtitles/components/assets-view.tsx`
14. `external/opencut-classic/apps/web/src/subtitles/insert.ts`
15. `external/opencut-classic/apps/web/src/subtitles/build-subtitle-text-element.ts`
16. `external/opencut-classic/apps/web/src/components/editor/panels/properties/registry.tsx`
17. `backend/app/routers/transcription.py`
18. `backend/app/routers/speech.py`
19. `backend/services/model_cache_policy.py`

## 17. Minimal code skeletons

### 17.1 OmniVoice client

```ts
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

export function getOmniVoiceBaseUrl() {
  if (typeof window === "undefined") return DEFAULT_BASE_URL;
  return (
    window.localStorage.getItem("omnivoice.apiBaseUrl") ||
    process.env.NEXT_PUBLIC_OMNIVOICE_API_BASE_URL ||
    DEFAULT_BASE_URL
  ).replace(/\/+$/, "");
}

export async function omniVoiceFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${getOmniVoiceBaseUrl()}${path}`, {
    ...init,
    headers: {
      "ngrok-skip-browser-warning": "true",
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(detail || `OmniVoice request failed: ${response.status}`);
  }
  return response;
}
```

### 17.2 SRT transcription adapter

```ts
export async function transcribeBlobToSrt({
  audioBlob,
  language,
}: {
  audioBlob: Blob;
  language?: string;
}) {
  const form = new FormData();
  form.append("file", audioBlob, "timeline.wav");
  form.append("model", "Systran/faster-whisper-large-v3");
  form.append("response_format", "srt");
  form.append("word_timestamps", "true");
  if (language && language !== "auto") form.append("language", language);

  const response = await omniVoiceFetch("/v1/audio/transcriptions", {
    method: "POST",
    body: form,
  });
  return response.text();
}
```

### 17.3 Insert TTS audio element

```ts
async function addGeneratedAudioToTimeline({
  editor,
  projectId,
  file,
  startSeconds,
  durationSeconds,
}: {
  editor: EditorCore;
  projectId: string;
  file: File;
  startSeconds: number;
  durationSeconds: number;
}) {
  const asset = await editor.media.addMediaAsset({
    projectId,
    asset: {
      name: file.name,
      type: "audio",
      file,
      url: URL.createObjectURL(file),
      duration: durationSeconds,
    },
  });
  if (!asset) return;

  editor.timeline.insertElement({
    element: {
      type: "audio",
      sourceType: "upload",
      mediaId: asset.id,
      name: asset.name,
      startTime: mediaTimeFromSeconds({ seconds: startSeconds }),
      duration: mediaTimeFromSeconds({ seconds: durationSeconds }),
      trimStart: ZERO_MEDIA_TIME,
      trimEnd: ZERO_MEDIA_TIME,
      params: {
        ...DEFAULTS.audio.element.params,
      },
    },
    placement: { mode: "auto", trackType: "audio" },
  });
}
```

Verify exact `DEFAULTS.audio.element.params` before using this skeleton.

## 18. Decision checklist before replacing current `video-editor`

Use `opencut-classic` if:

- Need a working timeline editor now.
- Accept archived upstream.
- Accept Next.js web app as main integration surface.
- Desktop can come later via wrapper or separate plan.

Avoid `opencut-classic` if:

- Need actively maintained upstream.
- Need Tauri-first architecture immediately.
- Need server-side, deterministic FFmpeg export immediately.
- Need native desktop app now.

## 19. Recommended next action

Before replacing current `video-editor` again:

1. Run `opencut-classic` locally from `external/opencut-classic`.
2. Import a video.
3. Add it to timeline.
4. Generate/import captions.
5. Export short MP4.
6. If those pass, replace `video-editor/` with `opencut-classic`.
7. Start Phase 1 OmniVoice settings tab.
