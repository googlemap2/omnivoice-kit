import argparse
import json
import random
from pathlib import Path


def read_text(txt_path: Path) -> str:
    return txt_path.read_text(encoding="utf-8").strip()


def collect_audio_files(audio_dir: Path):
    # Accept .wav/.WAV consistently across OS and upload tools.
    return sorted([p for p in audio_dir.iterdir() if p.is_file() and p.suffix.lower() == ".wav"])


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

    wavs = collect_audio_files(audio_dir)
    items = []
    missing_text = []
    empty_text = []
    for wav in wavs:
        txt = text_dir / f"{wav.stem}.txt"
        if not txt.is_file():
            missing_text.append(wav.name)
            continue
        text = read_text(txt)
        if not text:
            empty_text.append(txt.name)
            continue
        items.append(
            {
                "id": wav.stem,
                "audio_path": str(wav.resolve()),
                "text": text,
                "language_id": args.language_id,
            }
        )

    if missing_text:
        print(f"Skipped {len(missing_text)} audio files without matching .txt:")
        for name in missing_text:
            print(f"  - {name}")
    if empty_text:
        print(f"Skipped {len(empty_text)} empty transcript files:")
        for name in empty_text:
            print(f"  - {name}")

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
