# OmniVoice Voice Clone Kit

Project riêng cho nhu cầu clone giọng TTS với OmniVoice.

## 1) Cài đặt

```bash
cd omnivoice-voice-clone-kit
uv sync
```

Hoặc dùng pip:

```bash
pip install -r requirements.txt
```

Đồng bộ `requirements.txt` theo `uv.lock`:

```bash
uv export --format requirements-txt --no-hashes -o requirements.txt
```

Model được tải và load **trong thư mục `models/` của project** (không dùng `~/.cache/huggingface` mặc định):

- Snapshot model (weights + config): `models/models--<org>--<name>/`
  - OmniVoice: `models/models--k2-fsa--OmniVoice/`
  - ASR: `models/models--Systran--faster-whisper-large-v3/` (và các biến thể khác)
- Cache phụ của Hugging Face Hub (nếu cần): `models/.hf_home/hub/`

Lần chạy đầu (UI **Install Default Model**, API `/v1/model-status/install`, hoặc infer lần đầu) sẽ tự `snapshot_download` vào `models/models--...`.

Cài thủ công trước khi chạy:

```bash
uv run python -c "from voicekit.model_store import install_model; install_model('k2-fsa/OmniVoice')"
uv run python -c "from voicekit.model_store import install_model; install_model('Systran/faster-whisper-large-v3')"
```

Nếu truyền `--model` là đường dẫn local (ví dụ `models/OmniVoice`) thì sẽ ưu tiên load từ đường dẫn đó.

## 2) Chạy Web UI

### Google Colab backend + ngrok

Mở notebook [`colab_backend_ngrok.ipynb`](colab_backend_ngrok.ipynb) trên Google Colab để clone/pull source,
cài dependencies, chạy FastAPI backend và expose URL bằng ngrok. Model sẽ tự tải vào thư mục `models/`
của runtime Colab khi cần.

### Next.js (khuyến nghị)

Terminal 1 — API backend:

```bash
uv run uvicorn voicekit.api:app --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
cp .env.local.example .env.local
pnpm install
pnpm dev
```

Mở trình duyệt: `http://localhost:3000`

Chi tiết: [frontend/README.md](frontend/README.md)

### Gradio (legacy)

```bash
uv run voicekit-ui
```

Mở trình duyệt: `http://127.0.0.1:7861`

Web UI đã tách 2 tab riêng:
- `TTS by Speaker ID`: dùng prompt đã lưu trong `speakers.json`
- `Clone by Reference Audio`: upload wav mỗi lần infer

Đã bổ sung các tham số generation học từ project gốc:
- `instruct` (voice design mo rong)
- `speed`, `duration`
- `denoise`, `preprocess_prompt`, `postprocess_output`
- `effect_preset`: `raw`, `normalize`, `broadcast`

Tab `Transcription` dùng `faster-whisper` để chuyển audio/video thành text,
JSON, SRT hoặc VTT. Với input không phải WAV, cần cài `ffmpeg` và để trong PATH.

Tab `Translation` dùng translation provider registry (mặc định `passthrough` giữ nguyên text).
Có thể dịch plain text hoặc mảng segments JSON (phục vụ dubbing sau này).

## 3) Chạy CLI clone giọng nhanh

```bash
python -m voicekit.scripts.clone_tts \
  --text "Xin chao, day la ban clone giong." \
  --ref_audio path/to/ref.wav \
  --output out.wav \
  --num_step 32
```

Tùy chọn:
- `--ref_text "noi dung file ref"`: nếu muốn nhập transcript tay.
- `--language vi` hoặc `--language en`
- `--instruct "female, low pitch, british accent"`
- `--speed 1.0`, `--duration 8.0`
- `--denoise true|false`
- `--preprocess_prompt true|false`
- `--postprocess_output true|false`
- `--effect-preset raw|normalize|broadcast`
- `--device cpu|cuda|mps`

CLI tổng hợp theo 3 tab web (không cần mở UI):

### 3.1 TTS by Speaker ID

```bash
uv run voicekit speaker-id \
  --speaker_id my_voice \
  --text "Xin chao, day la test speaker id." \
  --output out_speaker_id.wav
```

Đầy đủ tham số:

```bash
uv run voicekit speaker-id \
  --speaker_id my_voice \
  --speakers speakers.json \
  --text "Xin chao, day la test speaker id." \
  --output out_speaker_id_full.wav \
  --model k2-fsa/OmniVoice \
  --language vi \
  --instruct-item female \
  --instruct-item low pitch \
  --num_step 16 \
  --guidance_scale 2.0 \
  --speed 1.0 \
  --duration 8.0 \
  --denoise true \
  --preprocess_prompt true \
  --postprocess_output true \
  --effect-preset raw \
  --device cuda
```

### 3.2 Clone by Reference Audio

```bash
uv run voicekit ref-audio \
  --text "Xin chao, day la test ref audio." \
  --ref_audio assets/voices/ref.wav \
  --ref_text "xin chao day la mau giong" \
  --output out_ref.wav
```

Đầy đủ tham số:

```bash
uv run voicekit ref-audio \
  --text "Xin chao, day la test ref audio." \
  --ref_audio assets/voices/ref.wav \
  --ref_text "xin chao day la mau giong" \
  --output out_ref_full.wav \
  --model k2-fsa/OmniVoice \
  --language vi \
  --instruct-item female \
  --instruct-item middle-aged \
  --num_step 16 \
  --guidance_scale 2.0 \
  --speed 1.0 \
  --duration 8.0 \
  --denoise true \
  --preprocess_prompt true \
  --postprocess_output true \
  --effect-preset raw \
  --device cuda
```

### 3.3 Voice Design

```bash
uv run voicekit voice-design \
  --text "Xin chao, toi la giong nu trung nien." \
  --instruct-item female \
  --instruct-item middle-aged \
  --output out_voice_design.wav
```

Đầy đủ tham số:

```bash
uv run voicekit voice-design \
  --text "Xin chao, toi la giong nu trung nien." \
  --output out_voice_design_full.wav \
  --model k2-fsa/OmniVoice \
  --language vi \
  --instruct-item female \
  --instruct-item middle-aged \
  --num_step 16 \
  --guidance_scale 2.0 \
  --speed 1.0 \
  --duration 8.0 \
  --denoise true \
  --postprocess_output true \
  --effect-preset raw \
  --device cuda
```

Gợi ý:
- `--instruct-item` có thể truyền nhiều lần để ghép style.
- Không mix item tiếng Anh và tiếng Trung trong cùng 1 lệnh.
- Các tham số chung: `--num_step`, `--guidance_scale`, `--speed`, `--duration`, `--denoise`, `--postprocess_output`, `--device`.

### 3.4 Transcribe audio/video

```bash
uv run voicekit transcribe \
  --input path/to/audio.wav \
  --language vi \
  --format text
```

Xuất SRT:

```bash
uv run voicekit transcribe \
  --input path/to/audio.wav \
  --language vi \
  --format srt \
  --output transcript.srt
```

### 3.4.1 Import/export subtitles

Import SRT/VTT to JSON segments:

```bash
uv run voicekit subtitle-import \
  --input transcript.srt \
  --output transcript_segments.json
```

Export JSON segments back to SRT/VTT:

```bash
uv run voicekit subtitle-export \
  --input transcript_segments.json \
  --format vtt \
  --output transcript.vtt
```

### 3.5 Translate text hoặc segments

Dịch plain text (provider mặc định `passthrough` trả nguyên văn để test pipeline):

```bash
uv run voicekit translate \
  --text "Xin chao, day la ban test dich." \
  --source-language vi \
  --target-language en \
  --provider passthrough
```

Dịch segments từ JSON (ví dụ output verbose JSON của transcribe):

```bash
uv run voicekit translate \
  --segments-json transcript_segments.json \
  --source-language vi \
  --target-language en \
  --provider passthrough \
  --output translated.json
```

### 3.6 Dub audio/video v1

Pipeline dubbing v1 chạy tuần tự: extract audio bằng FFmpeg, transcribe, translate,
generate TTS cho từng segment bằng một voice profile, mix WAV, export SRT/VTT và
cố gắng mux video nếu input có video stream.

```bash
uv run voicekit dub \
  --input path/to/video.mp4 \
  --voice yen \
  --source-language en \
  --target-language vi \
  --provider passthrough \
  --folder-name video-demo \
  --output-dir outputs/dubbing
```

Kết quả trả JSON gồm đường dẫn `dubbed_audio_path`, `dubbed_video_path`,
`srt_path`, và `vtt_path`. Nếu không truyền `--folder-name`, output subfolder
sẽ dùng tên file input và tự thêm số tăng dần khi trùng, ví dụ
`video`, `video-2`, `video-3`.

Chạy thêm speaker diarization nếu đã cài `pyannote.audio`, có Hugging Face token
trong Settings hoặc env `HF_TOKEN`/`HUGGINGFACE_TOKEN`, và đã accept user
conditions cho các gated model pyannote:

- `pyannote/speaker-diarization-3.1`
- `pyannote/segmentation-3.0`
- `pyannote/speaker-diarization-community-1`

```bash
uv run voicekit dub \
  --input path/to/video.mp4 \
  --voice yen \
  --source-language en \
  --target-language vi \
  --diarize
```

Model diarization cũng được snapshot vào thư mục model của project:

```text
models/models--pyannote--speaker-diarization-3.1/
```

Cache phụ của Hugging Face/pyannote vẫn nằm trong:

```text
models/.hf_home/hub/
```

Chạy diarization riêng:

```bash
uv run voicekit diarize \
  --input path/to/audio.wav \
  --output speakers.json
```

Provider có sẵn: `passthrough`, `google` (qua `deep-translator`, không cần API key), `nllb`
(cần `transformers` + model trong `models/`), `deepl`, `microsoft`, `mymemory` (ba provider cuối
cần API key trong settings, chưa implement đầy đủ).

Cấu hình provider trong tab **Settings** → **Translation provider API keys** (lưu vào `data/settings.json`), hoặc chỉnh file trực tiếp:

```json
{
  "default_translation_provider": "passthrough",
  "translation_provider_config": {
    "deepl": {"api_key": "YOUR_KEY"},
    "google": {"api_key": "", "disabled": false},
    "microsoft": {"api_key": "YOUR_KEY", "region": "global"},
    "mymemory": {"api_key": ""},
    "nllb": {"model_id": "facebook/nllb-200-distilled-600M"}
  }
}
```

## 4) Gợi ý chất lượng

- Reference audio nên dài `3-10 giây`, giọng rõ, ít tạp âm.
- Text ngắn trước để test pipeline, sau đó tăng độ dài.
- CPU chạy được nhưng chậm hơn GPU đáng kể.

## 5) Chạy OpenAI-compatible Speech API

Chạy local API server:

```bash
uv run uvicorn voicekit.api:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Liệt kê voice profile:

```bash
curl http://127.0.0.1:8000/v1/voices
```

Kiểm tra trạng thái model local:

```bash
curl http://127.0.0.1:8000/v1/model-status
```

Xem lịch sử generation:

```bash
curl http://127.0.0.1:8000/v1/generation-history
```

Xem/cập nhật settings:

```bash
curl http://127.0.0.1:8000/v1/settings
```

```bash
curl -X PUT http://127.0.0.1:8000/v1/settings \
  -H "Content-Type: application/json" \
  -d '{
    "default_model": "k2-fsa/OmniVoice",
    "default_device": "",
    "default_effect_preset": "raw",
    "output_dir": "outputs"
  }'
```

Cài model mặc định nếu còn thiếu:

```bash
curl -X POST http://127.0.0.1:8000/v1/model-status/install \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "k2-fsa/OmniVoice"}'
```

Generate WAV qua endpoint kiểu OpenAI:

```bash
curl -X POST http://127.0.0.1:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -o api_speech.wav \
  -d '{
    "model": "k2-fsa/OmniVoice",
    "voice": "yen",
    "input": "Xin chao, day la audio tao tu local API.",
    "language": "vi",
    "num_step": 4,
    "effect_preset": "raw",
    "response_format": "wav"
  }'
```

Hiện endpoint speech hỗ trợ `wav` trước. Các format khác sẽ thêm sau khi có audio export layer.

Transcribe audio qua endpoint kiểu OpenAI:

```bash
curl -X POST http://127.0.0.1:8000/v1/audio/transcriptions \
  -F "file=@path/to/audio.wav" \
  -F "model=Systran/faster-whisper-large-v3" \
  -F "language=vi" \
  -F "response_format=verbose_json"
```

Các `response_format` đang hỗ trợ: `json`, `text`, `verbose_json`, `srt`, `vtt`.

Import subtitle file:

```bash
curl -X POST http://127.0.0.1:8000/v1/subtitles/import \
  -F "file=@transcript.srt" \
  -F "format=srt"
```

Export subtitle segments:

```bash
curl -X POST http://127.0.0.1:8000/v1/subtitles/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "srt",
    "segments": [
      {"id": 0, "start": 0.0, "end": 1.5, "text": "Xin chao"},
      {"id": 1, "start": 1.5, "end": 3.0, "text": "the gioi"}
    ]
  }'
```

Dub uploaded media through API:

```bash
curl -X POST http://127.0.0.1:8000/v1/dubbing/dub-upload \
  -F "file=@path/to/video.mp4" \
  -F "voice=yen" \
  -F "source_language=en" \
  -F "target_language=vi" \
  -F "translation_provider=passthrough"
```

Run speaker diarization through API:

```bash
curl -X POST http://127.0.0.1:8000/v1/diarization/diarize \
  -F "file=@path/to/audio.wav"
```

Liệt kê translation providers:

```bash
curl http://127.0.0.1:8000/v1/translation/providers
```

Dịch text:

```bash
curl -X POST http://127.0.0.1:8000/v1/translation/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Xin chao, day la ban test dich.",
    "source_language": "vi",
    "target_language": "en",
    "provider": "passthrough"
  }'
```

Dịch segments:

```bash
curl -X POST http://127.0.0.1:8000/v1/translation/translate \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {"id": 0, "start": 0.0, "end": 1.5, "text": "Xin chao"},
      {"id": 1, "start": 1.5, "end": 3.0, "text": "the gioi"}
    ],
    "source_language": "vi",
    "target_language": "en",
    "provider": "passthrough"
  }'
```

## 6) Speaker ID riêng không fine-tune

Bạn có thể dùng `speaker_id` ảo bằng cách lưu `voice_clone_prompt` (token prompt) từ 1 file wav mẫu.

### 6.1 Tạo prompt từ wav

Lưu full prompt (.pt):

```bash
python -m voicekit.scripts.build_speaker_prompt \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.pt
```

Hoặc lưu token (.npy + .json metadata):

```bash
python -m voicekit.scripts.build_speaker_prompt \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.npy
```

### 6.2 Tạo registry speaker_id

Copy `speakers.example.json` thành `speakers.json`, ví dụ:

```json
{
  "my_voice": {
    "prompt_path": "assets/speakers/my_voice.pt",
    "language": "vi"
  }
}
```

### 6.3 Infer bằng speaker_id

```bash
python -m voicekit.scripts.clone_tts_with_speaker_id \
  --speaker_id my_voice \
  --text "Xin chao, day la speaker id ao khong can fine tune." \
  --speakers speakers.json \
  --output out.wav
```

## 7) Backup model Hugging Face để tránh bị xóa repo

Tạo snapshot local + manifest checksum:

```bash
python backup_model.py \
  --repo-id k2-fsa/OmniVoice \
  --revision main \
  --local-dir models/models--k2-fsa--OmniVoice
```

Script sẽ:
- Pin về commit hash cụ thể (không phụ thuộc `main` sau này)
- Lưu manifest `models/models--k2-fsa--OmniVoice/backup_manifest.json` (mặc định nếu không truyền `--local-dir`)
- Ghi SHA256 cho từng file để verify

Kiểm tra toàn vẹn sau khi copy/restore:

```bash
python verify_checksum.py --model-dir models/models--k2-fsa--OmniVoice
```

Nên lưu trữ thêm 1 bản archive:

```powershell
Compress-Archive -Path models/models--k2-fsa--OmniVoice/* -DestinationPath model_backup_omnivoice.zip -Force
```
