import argparse
import json
import random
from pathlib import Path


def read_text_utf8(path: Path) -> str:
    # utf-8-sig handles BOM files from Windows editors
    return path.read_text(encoding="utf-8-sig").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare train/dev manifest JSONL for OmniVoice fine-tuning")
    parser.add_argument("--audio_dir", required=True, type=Path)
    parser.add_argument("--text_dir", required=True, type=Path)
    parser.add_argument("--out_dir", required=True, type=Path)
    parser.add_argument("--language_id", default="vi")
    parser.add_argument("--dev_ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    audio_dir = args.audio_dir.resolve()
    text_dir = args.text_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(audio_dir.glob("*.wav"))
    if not wav_files:
        raise FileNotFoundError(f"No .wav files found in {audio_dir}")

    samples = []
    for wav_path in wav_files:
        sample_id = wav_path.stem
        txt_path = text_dir / f"{sample_id}.txt"
        if not txt_path.exists():
            continue

        text = read_text_utf8(txt_path)
        if not text:
            continue

        samples.append(
            {
                "id": sample_id,
                "audio_path": str(wav_path.resolve()),
                "text": text,
                "language_id": args.language_id,
            }
        )

    if len(samples) < 2:
        raise RuntimeError(
            "Need at least 2 valid samples (wav+txt) to split train/dev. "
            f"Found: {len(samples)}"
        )

    random.seed(args.seed)
    random.shuffle(samples)

    dev_size = max(1, int(len(samples) * args.dev_ratio))
    dev_size = min(dev_size, len(samples) - 1)

    dev_samples = samples[:dev_size]
    train_samples = samples[dev_size:]

    train_path = out_dir / "train.jsonl"
    dev_path = out_dir / "dev.jsonl"

    with train_path.open("w", encoding="utf-8") as f:
        for item in train_samples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with dev_path.open("w", encoding="utf-8") as f:
        for item in dev_samples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(train_samples)} train samples -> {train_path}")
    print(f"Wrote {len(dev_samples)} dev samples   -> {dev_path}")


if __name__ == "__main__":
    main()
