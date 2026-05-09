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

Mo: `http://127.0.0.1:7861`

## 3) Chay CLI

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

Muc tieu la giong sat hon clone thuong, nhung khong the dam bao 100% tuyet doi.

Buoc A - Chuan bi du lieu:
- Dat wav vao `data/raw/audio/`
- Dat transcript txt cung ten file vao `data/raw/text/`
- Vi du: `001.wav` <-> `001.txt`

Buoc B - Tao manifest train/dev:

```bash
uv run python finetune/prepare_manifest.py \
  --audio_dir data/raw/audio \
  --text_dir data/raw/text \
  --out_dir data/finetune/manifests \
  --language_id vi \
  --dev_ratio 0.05
```

Buoc C - Chay fine-tune (PowerShell tren Windows):

```powershell
./finetune/run_finetune.ps1 -GpuIds "0" -NumGpus 1
```

Checkpoint se nam o: `exp/voice_clone_finetune`

Buoc D - Infer bang checkpoint da fine-tune:

```bash
uv run python clone_tts.py \
  --model exp/voice_clone_finetune/checkpoint-3000 \
  --text "Xin chao, day la giong sau fine-tune." \
  --ref_audio path/to/ref.wav \
  --output out_finetuned.wav \
  --device cuda
```
