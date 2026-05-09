import argparse
import json
import random
from pathlib import Path


def read_text(txt_path: Path) -> str:
    return txt_path.read_text(encoding="utf-8").strip()


def main():
    parser = argparse.ArgumentParser(description="Prepare train/dev JSONL for single-speaker fine-tuning")
    parser.add_argument("--audio_dir", type=str, required=True, help="Directory containing wav files")
    parser.add_argument("--text_dir", type=str, required=True, help="Directory containing txt files with same stem")
    parser.add_argument("--out_dir", type=str, default="data/finetune/manifests", help="Output directory for manifests")
    parser.add_argument("--language_id", type=str, default="vi", help="Language id, e.g. vi/en")
    parser.add_argument("--dev_ratio", type=float, default=0.05, help="Dev split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Shuffle seed")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    text_dir = Path(args.text_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wavs = sorted(audio_dir.glob("*.wav"))
    items = []
    for wav in wavs:
        txt = text_dir / f"{wav.stem}.txt"
        if not txt.is_file():
            continue
        text = read_text(txt)
        if not text:
            continue
        items.append(
            {
                "id": wav.stem,
                "audio_path": str(wav.resolve()),
                "text": text,
                "language_id": args.language_id,
            }
        )

    if len(items) < 20:
        raise ValueError("Need at least 20 valid samples (wav+txt) for a meaningful fine-tune.")

    rng = random.Random(args.seed)
    rng.shuffle(items)

    dev_n = max(1, int(len(items) * args.dev_ratio))
    dev = items[:dev_n]
    train = items[dev_n:]

    train_path = out_dir / "train.jsonl"
    dev_path = out_dir / "dev.jsonl"

    with train_path.open("w", encoding="utf-8") as f:
        for x in train:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    with dev_path.open("w", encoding="utf-8") as f:
        for x in dev:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    print(f"Prepared {len(train)} train / {len(dev)} dev samples")
    print(f"Train manifest: {train_path}")
    print(f"Dev manifest:   {dev_path}")


if __name__ == "__main__":
    main()
