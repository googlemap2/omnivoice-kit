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

Model được tải và load local trong project:
- Thư mục mặc định: `models/OmniVoice`
- Lần chạy đầu sẽ auto download từ Hugging Face vào thư mục này.
- Nếu truyền `--model` là đường dẫn local thì sẽ ưu tiên load từ đường dẫn đó.

## 2) Chạy Web UI

```bash
python app.py
```

Mở trình duyệt: `http://127.0.0.1:7861`

Web UI đã tách 2 tab riêng:
- `TTS by Speaker ID`: dùng prompt đã lưu trong `speakers.json`
- `Clone by Reference Audio`: upload wav mỗi lần infer

Đã bổ sung các tham số generation học từ project gốc:
- `instruct` (voice design mo rong)
- `speed`, `duration`
- `denoise`, `preprocess_prompt`, `postprocess_output`

## 3) Chạy CLI clone giọng nhanh

```bash
python clone_tts.py \
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
- `--device cpu|cuda|mps`

CLI tổng hợp theo 3 tab web (không cần mở UI):

### 3.1 TTS by Speaker ID

```bash
python omnivoice_cli.py speaker-id \
  --speaker_id my_voice \
  --text "Xin chao, day la test speaker id." \
  --output out_speaker_id.wav
```

Đầy đủ tham số:

```bash
python omnivoice_cli.py speaker-id \
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
  --device cuda
```

### 3.2 Clone by Reference Audio

```bash
python omnivoice_cli.py ref-audio \
  --text "Xin chao, day la test ref audio." \
  --ref_audio assets/voices/ref.wav \
  --ref_text "xin chao day la mau giong" \
  --output out_ref.wav
```

Đầy đủ tham số:

```bash
python omnivoice_cli.py ref-audio \
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
  --device cuda
```

### 3.3 Voice Design

```bash
python omnivoice_cli.py voice-design \
  --text "Xin chao, toi la giong nu trung nien." \
  --instruct-item female \
  --instruct-item middle-aged \
  --output out_voice_design.wav
```

Đầy đủ tham số:

```bash
python omnivoice_cli.py voice-design \
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
  --device cuda
```

Gợi ý:
- `--instruct-item` có thể truyền nhiều lần để ghép style.
- Không mix item tiếng Anh và tiếng Trung trong cùng 1 lệnh.
- Các tham số chung: `--num_step`, `--guidance_scale`, `--speed`, `--duration`, `--denoise`, `--postprocess_output`, `--device`.
- Bật dịch trước khi TTS với NLLB: `--translate true --nllb-source-lang eng_Latn --nllb-target-lang vie_Latn`.

Ví dụ dịch Anh -> Việt rồi mới TTS:

```bash
python omnivoice_cli.py ref-audio \
  --text "Hello everyone, this is a demo." \
  --ref_audio assets/voices/ref.wav \
  --output out_ref_vi.wav \
  --translate true \
  --nllb-source-lang eng_Latn \
  --nllb-target-lang vie_Latn \
  --nllb-model facebook/nllb-200-distilled-600M
```

## 4) Gợi ý chất lượng

- Reference audio nên dài `3-10 giây`, giọng rõ, ít tạp âm.
- Text ngắn trước để test pipeline, sau đó tăng độ dài.
- CPU chạy được nhưng chậm hơn GPU đáng kể.

## 5) Speaker ID riêng không fine-tune

Bạn có thể dùng `speaker_id` ảo bằng cách lưu `voice_clone_prompt` (token prompt) từ 1 file wav mẫu.

### 5.1 Tạo prompt từ wav

Lưu full prompt (.pt):

```bash
python build_speaker_prompt.py \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.pt
```

Hoặc lưu token (.npy + .json metadata):

```bash
python build_speaker_prompt.py \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.npy
```

### 5.2 Tạo registry speaker_id

Copy `speakers.example.json` thành `speakers.json`, ví dụ:

```json
{
  "my_voice": {
    "prompt_path": "assets/speakers/my_voice.pt",
    "language": "vi"
  }
}
```

### 5.3 Infer bằng speaker_id

```bash
python clone_tts_with_speaker_id.py \
  --speaker_id my_voice \
  --text "Xin chao, day la speaker id ao khong can fine tune." \
  --speakers speakers.json \
  --output out.wav
```

## 6) Backup model Hugging Face để tránh bị xóa repo

Tạo snapshot local + manifest checksum:

```bash
python backup_model.py \
  --repo-id k2-fsa/OmniVoice \
  --revision main \
  --local-dir models/OmniVoice
```

Script sẽ:
- Pin về commit hash cụ thể (không phụ thuộc `main` sau này)
- Lưu manifest `models/OmniVoice/backup_manifest.json`
- Ghi SHA256 cho từng file để verify

Kiểm tra toàn vẹn sau khi copy/restore:

```bash
python verify_checksum.py --model-dir models/OmniVoice
```

Nên lưu trữ thêm 1 bản archive:

```powershell
Compress-Archive -Path models/OmniVoice/* -DestinationPath model_backup_omnivoice.zip -Force
```
