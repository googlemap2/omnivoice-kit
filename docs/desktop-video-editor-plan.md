# Desktop Video Editor Plan

Tài liệu này mô tả hướng xây dựng desktop app đa nền tảng cho OmniVoice Kit theo kiến trúc client-server:

- `backend/`: FastAPI server chạy AI/model/job nặng.
- `desktop/`: Tauri desktop app làm giao diện video editor và gọi API backend.
- `frontend/`: web studio hiện tại, có thể giữ riêng hoặc tái sử dụng từng phần UI/logic cho desktop.

## Mục Tiêu Sản Phẩm

Desktop app tập trung vào workflow edit video có AI hỗ trợ:

- Import video/audio/subtitle local.
- Preview video và timeline.
- Cắt, split, trim, sắp xếp clip.
- Tạo transcription/subtitle từ backend ASR.
- Dịch subtitle bằng provider model.
- Tạo voice/dubbing bằng backend OmniVoice.
- Export video final bằng FFmpeg.

Backend không được bundle vào desktop trong giai đoạn này. Desktop chỉ gọi backend server qua URL do người dùng cấu hình.

## Tech Stack Đề Xuất

### Desktop Shell

- Tauri 2.
- Rust sidecar/native layer cho:
  - File picker.
  - File system access.
  - App config local.
  - Chạy FFmpeg local nếu export trên máy người dùng.
  - Native menu/window/update sau này.

### UI

- React + Vite.
- TypeScript.
- MUI nếu muốn giữ style và component pattern hiện tại.
- Zustand cho editor state/timeline state.
- TanStack Query hoặc fetch wrapper riêng cho API state nếu cần cache/request status rõ ràng.

### Video/Audio Engine

- HTML `<video>` cho preview phase đầu.
- Canvas/SVG overlay cho playhead, captions, selection box.
- FFmpeg sidecar cho:
  - Probe media metadata.
  - Generate thumbnails.
  - Generate waveform/proxy audio.
  - Cut/merge/export.
- Không xử lý encode/decode nặng bằng JavaScript thuần.

### Backend API

- FastAPI server hiện có.
- Desktop gọi các endpoint:
  - `/health`
  - `/v1/audio/transcriptions`
  - `/v1/translation`
  - `/v1/audio/speech`
  - `/v1/audio/speech/emotion-script`
  - `/v1/dubbing`
  - `/v1/jobs`
  - `/v1/provider-models`
- Backend URL phải là runtime config, không hardcode build-time.

### Project Format

- Project file dạng JSON.
- Lưu metadata timeline, asset path, subtitle track, generated voice paths, export settings.
- Media gốc vẫn nằm ở local path của người dùng; project chỉ reference path.

Ví dụ format tối thiểu:

```json
{
  "version": 1,
  "name": "Demo Project",
  "backendUrl": "https://example.ngrok-free.dev",
  "assets": [],
  "timeline": {
    "tracks": []
  },
  "export": {
    "format": "mp4",
    "resolution": "1920x1080",
    "fps": 30
  }
}
```

## Phase 1: Desktop Foundation

Mục tiêu: tạo được app desktop mở lên, cấu hình backend URL và test kết nối.

- [x] Tạo folder `desktop/`.
- [x] Scaffold Tauri 2 + React + Vite + TypeScript.
- [x] Thêm màn hình onboarding/settings cho Backend URL.
- [x] Lưu Backend URL vào local app config.
- [x] Gọi `/health` để test connection.
- [x] Hiển thị trạng thái backend: connected, disconnected, error message.
- [x] Tạo API client dùng runtime Backend URL.
- [x] Thêm dev script chạy desktop app.

Success criteria:

- App chạy được trên Windows dev machine.
- Người dùng nhập ngrok/server URL và test connection thành công.
- Không phụ thuộc `NEXT_PUBLIC_API_BASE_URL`.

## Phase 2: Media Import And Preview

Mục tiêu: import video local và preview cơ bản.

- [ ] Thêm file picker chọn video/audio.
- [ ] Lưu asset metadata vào project state.
- [ ] Preview video bằng `<video>`.
- [ ] Đọc duration, resolution, filename, size.
- [ ] Thêm media bin hiển thị danh sách assets.
- [ ] Tạo project mới và mở project JSON.
- [ ] Lưu project JSON.

Success criteria:

- Import được video local.
- Preview play/pause/seek được.
- Save/open project giữ lại asset references.

## Phase 3: Timeline Core

Mục tiêu: có timeline editor tối thiểu để thao tác clip.

- [ ] Tạo timeline data model: tracks, clips, start, duration, source range.
- [ ] Drag asset vào timeline.
- [ ] Playhead sync với video preview.
- [ ] Trim đầu/cuối clip.
- [ ] Split clip tại playhead.
- [ ] Move clip trong cùng track.
- [ ] Zoom timeline.
- [ ] Undo/redo tối thiểu cho edit operations.

Success criteria:

- Người dùng cắt/split/sắp xếp clip trong timeline.
- State timeline serializable vào project JSON.

## Phase 4: Subtitle And Transcription

Mục tiêu: gọi backend ASR để tạo subtitle track.

- [ ] Upload hoặc gửi file path phù hợp tới backend transcription endpoint.
- [ ] Gọi `/v1/audio/transcriptions` với job mode nếu file dài.
- [ ] Poll `/v1/jobs/{job_id}` khi backend trả job.
- [ ] Convert segments thành subtitle track.
- [ ] Hiển thị subtitle overlay trong preview.
- [ ] Cho phép edit text/timing subtitle.
- [ ] Import/export SRT/VTT nếu cần.

Success criteria:

- Từ video/audio, tạo được subtitle track.
- Subtitle sync với playhead và editable.

## Phase 5: Translation And Provider Models

Mục tiêu: dịch subtitle bằng backend/provider model.

- [ ] Load provider list từ `/v1/provider-models`.
- [ ] Chọn provider/model trong desktop settings hoặc project panel.
- [ ] Gửi subtitle segments tới translation endpoint.
- [ ] Tạo translated subtitle track riêng.
- [ ] Cho phép so sánh source/translated text.
- [ ] Lưu translation metadata vào project.

Success criteria:

- Dịch được toàn bộ subtitle track.
- Có thể chuyển preview giữa original subtitle và translated subtitle.

## Phase 6: Voice And Dubbing

Mục tiêu: tạo voice/dubbing bằng backend AI và gắn vào timeline.

- [ ] Load voice profiles từ backend.
- [ ] Tạo TTS cho từng subtitle segment hoặc selected text.
- [ ] Gọi `/v1/audio/speech` hoặc `/v1/audio/speech/emotion-script`.
- [ ] Poll job nếu dùng async workflow.
- [ ] Import generated audio vào media bin.
- [ ] Tự tạo audio clips trên timeline theo subtitle timing.
- [ ] Hỗ trợ preview mixed audio đơn giản.

Success criteria:

- Tạo được voice track từ subtitle/translation.
- Audio generated được đưa vào timeline đúng timing.

## Phase 7: Local Export With FFmpeg

Mục tiêu: render/export video final trên máy desktop.

- [ ] Bundle hoặc detect FFmpeg.
- [ ] Probe FFmpeg availability trong Tauri native layer.
- [ ] Generate FFmpeg command/filtergraph từ timeline.
- [ ] Export MP4 với video/audio/subtitle burn-in hoặc subtitle sidecar.
- [ ] Hiển thị progress export.
- [ ] Log command và lỗi export để debug.

Success criteria:

- Export được file MP4 từ timeline.
- Lỗi FFmpeg được hiển thị rõ, không silent fail.

## Phase 8: Packaging And Distribution

Mục tiêu: build installer đa nền tảng.

- [ ] Build Windows installer.
- [ ] Build macOS app nếu có môi trường ký/sign.
- [ ] Build Linux AppImage/deb nếu cần.
- [ ] Thiết lập app icon, app name, version.
- [ ] Quyết định update flow.
- [ ] Kiểm tra app data path cho config/project cache.
- [ ] Viết hướng dẫn cài đặt backend server riêng.

Success criteria:

- Có artifact install được.
- User cài desktop app, nhập backend URL, dùng được workflow cơ bản.

## Backend Requirements For Desktop

Backend cần ổn định các điểm sau để desktop gọi tốt:

- CORS cho desktop/web origins.
- `/health` trả nhanh, không load model.
- Job API đủ rõ: status, progress, result, error.
- File output URL có thể truy cập từ desktop.
- Error response thống nhất dạng `{"detail": "..."}` hoặc schema rõ hơn.
- Diagnostics có runtime memory/model status để debug server.

## Desktop Runtime Config

Config local tối thiểu:

```json
{
  "backendUrl": "http://127.0.0.1:8000",
  "ffmpegPath": "",
  "lastProjectPath": "",
  "theme": "system"
}
```

Không dùng biến môi trường build-time để quyết định backend URL trong desktop app.

## Rủi Ro Kỹ Thuật

- Timeline video editor dễ phình scope; cần giữ phase đầu cực nhỏ.
- Preview bằng browser video không đảm bảo frame-accurate ở phase đầu.
- FFmpeg filtergraph sẽ phức tạp khi nhiều track/effect.
- File path local khác nhau giữa Windows/macOS/Linux.
- Backend server có thể xử lý file upload lớn chậm hoặc timeout nếu chưa dùng job mode.
- Nếu backend chạy Colab/ngrok, link có thể đổi và cần UI reconnect rõ ràng.

## Quyết Định Hiện Tại

- Chọn Tauri thay vì Electron.
- Desktop không bundle backend/model.
- Backend chạy server riêng.
- Desktop gọi API backend qua runtime Backend URL.
- FFmpeg là engine export/transcode chính.
- Phase đầu ưu tiên: connection settings, import media, preview, timeline tối thiểu.
