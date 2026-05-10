# OmniVoice Voice Clone Kit

Project rieng cho nhu cau clone giong TTS voi OmniVoice.

## 1) Cai dat

```bash
cd omnivoice-voice-clone-kit
uv sync
```

Hoac dung pip:

```bash
pip install -r requirements.txt
```

Dong bo `requirements.txt` theo `uv.lock`:

```bash
uv export --format requirements-txt --no-hashes -o requirements.txt
```

## 2) Chay Web UI

```bash
python app.py
```

Mo trinh duyet: `http://127.0.0.1:7861`

## 3) Chay CLI clone giong nhanh

```bash
python clone_tts.py \
  --text "Xin chao, day la ban clone giong." \
  --ref_audio path/to/ref.wav \
  --output out.wav \
  --num_step 16
```

Tuy chon:
- `--ref_text "noi dung file ref"`: neu muon nhap transcript tay.
- `--language vi` hoac `--language en`
- `--device cpu|cuda|mps`

## 4) Goi y chat luong

- Reference audio nen dai `3-10 giay`, giong ro, it tap am.
- Text ngan truoc de test pipeline, sau do tang do dai.
- CPU chay duoc nhung cham hon GPU dang ke.

## 5) Fine-tune 1 giong (speaker-specific)

### 5.1 Chuan bi du lieu

Cau truc du lieu de tao token:

- `data/raw/audio/*.wav`
- `data/raw/text/*.txt`

Ten file phai trung nhau:
- `001.wav` <-> `001.txt`

### 5.2 Tao manifest train/dev

Lenh nhanh (khuyen nghi):

```powershell
./finetune/run_prepare_manifest.ps1
```

Tuy chinh tham so:

```powershell
./finetune/run_prepare_manifest.ps1 `
  -AudioDir data/raw/audio `
  -TextDir data/raw/text `
  -OutDir data/finetune/manifests `
  -LanguageId vi `
  -DevRatio 0.05
```

Lenh Python goc:

```bash
uv run python finetune/prepare_manifest.py \
  --audio_dir data/raw/audio \
  --text_dir data/raw/text \
  --out_dir data/finetune/manifests \
  --language_id vi \
  --dev_ratio 0.05
```

Ket qua:
- `data/finetune/manifests/train.jsonl`
- `data/finetune/manifests/dev.jsonl`

### 5.3 Tao token (Stage 1 local)

```powershell
./finetune/run_extract_tokens.ps1 -NjPerGpu 1 -SkipErrors
```

Ket qua chinh:
- `data/finetune/tokens/train/data.lst`
- `data/finetune/tokens/dev/data.lst`
- token shards trong `audios/` va `txts/`

### 5.4 Chay fine-tune (Stage 2)

```powershell
./finetune/run_finetune.ps1 -GpuIds "0" -NumGpus 1
```

Checkpoint mac dinh:
- `exp/voice_clone_finetune`

### 5.5 Infer bang checkpoint da fine-tune

```bash
uv run python clone_tts.py \
  --model exp/voice_clone_finetune/checkpoint-1200 \
  --text "Xin chao, day la giong sau fine-tune." \
  --ref_audio path/to/ref.wav \
  --output out_finetuned.wav \
  --language vi \
  --device cuda
```

## 6) Dung Colab cho Stage 2 (khuyen nghi)

Neu may local gap loi train tren Windows, ban co the:

1. Tao token local theo muc 5.3.
2. Zip token:

```powershell
Compress-Archive -Path data/finetune/tokens/* -DestinationPath tokens.zip -Force
```

3. Upload `tokens.zip` len Colab va dung notebook `colab_finetune_one_voice.ipynb`.

Notebook da duoc chinh de:
- Nap `tokens.zip`
- Chuan hoa cau truc `train/dev`
- Rewrite `data.lst` sang duong dan Linux (`/content/...`)
- Chay Stage 2 train

## 7) Luu y khi train

- Can GPU de train hieu qua.
- Neu OOM, giam `batch_tokens` trong `finetune/train_config_finetune_sdpa.json` (vi du 4096 hoac thap hon).
- Co the tang `gradient_accumulation_steps` de doi lay bo nho.
- Khuyen khich dat `HF_TOKEN` tren Colab de download model nhanh hon.

## 8) Speaker ID rieng khong fine-tune

Ban co the dung `speaker_id` ao bang cach luu `voice_clone_prompt` (token prompt) tu 1 file wav mau.

### 8.1 Tao prompt tu wav

Luu full prompt (.pt):

```bash
python build_speaker_prompt.py \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.pt
```

Hoac luu token (.npy + .json metadata):

```bash
python build_speaker_prompt.py \
  --ref_audio assets/voices/my_voice.wav \
  --ref_text "xin chao day la mau giong cua toi" \
  --out assets/speakers/my_voice.npy
```

### 8.2 Tao registry speaker_id

Copy `speakers.example.json` thanh `speakers.json`, vi du:

```json
{
  "my_voice": {
    "prompt_path": "assets/speakers/my_voice.pt",
    "language": "vi"
  }
}
```

### 8.3 Infer bang speaker_id

```bash
python clone_tts_with_speaker_id.py \
  --speaker_id my_voice \
  --text "Xin chao, day la speaker id ao khong can fine tune." \
  --speakers speakers.json \
  --output out.wav
```
