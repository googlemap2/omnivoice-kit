import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify model files against backup manifest checksums."
    )
    parser.add_argument(
        "--model-dir",
        required=True,
        help="Folder containing model snapshot and files referenced in manifest.",
    )
    parser.add_argument(
        "--manifest-name",
        default="backup_manifest.json",
        help="Manifest filename inside model-dir (default: backup_manifest.json).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir)
    manifest_path = model_dir / args.manifest_name

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", [])

    missing = []
    mismatched = []
    ok_count = 0

    for item in files:
        rel_path = item["path"]
        expected_sha = item["sha256"]
        target = model_dir / rel_path

        if not target.exists():
            missing.append(rel_path)
            continue

        actual_sha = sha256_file(target)
        if actual_sha != expected_sha:
            mismatched.append({"path": rel_path, "expected": expected_sha, "actual": actual_sha})
        else:
            ok_count += 1

    print(f"Manifest file count: {len(files)}")
    print(f"Verified OK: {ok_count}")
    print(f"Missing: {len(missing)}")
    print(f"Mismatched: {len(mismatched)}")

    if missing:
        print("\nMissing files:")
        for path in missing:
            print(f"- {path}")

    if mismatched:
        print("\nChecksum mismatch:")
        for item in mismatched:
            print(f"- {item['path']}")
            print(f"  expected: {item['expected']}")
            print(f"  actual:   {item['actual']}")

    if missing or mismatched:
        raise SystemExit(1)

    print("\nVerification passed.")


if __name__ == "__main__":
    main()
