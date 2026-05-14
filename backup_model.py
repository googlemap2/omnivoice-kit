import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from model_store import DEFAULT_HF_CACHE, configure_hf_local_cache


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(local_dir: Path, repo_id: str, commit_hash: str) -> dict:
    files = []
    for file_path in sorted(p for p in local_dir.rglob("*") if p.is_file()):
        rel = file_path.relative_to(local_dir).as_posix()
        files.append(
            {
                "path": rel,
                "size": file_path.stat().st_size,
                "sha256": sha256_file(file_path),
            }
        )

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    return {
        "repo_id": repo_id,
        "commit_hash": commit_hash,
        "generated_at_utc": generated_at,
        "file_count": len(files),
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and backup a full Hugging Face model snapshot."
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face model repo id, for example: k2-fsa/OmniVoice",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Branch, tag, or commit hash to snapshot (default: main).",
    )
    parser.add_argument(
        "--local-dir",
        default=None,
        help="Output folder for model snapshot. Default: models/<repo_name>",
    )
    parser.add_argument(
        "--manifest-name",
        default="backup_manifest.json",
        help="Manifest filename saved inside local-dir.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_hf_local_cache()

    repo_name = args.repo_id.split("/")[-1]
    local_dir = Path(args.local_dir) if args.local_dir else Path("models") / repo_name
    local_dir.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    repo_info = api.model_info(repo_id=args.repo_id, revision=args.revision)
    commit_hash = repo_info.sha

    snapshot_download(
        repo_id=args.repo_id,
        revision=commit_hash,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        cache_dir=str(DEFAULT_HF_CACHE),
    )

    manifest = build_manifest(local_dir=local_dir, repo_id=args.repo_id, commit_hash=commit_hash)
    manifest_path = local_dir / args.manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Backup completed: {local_dir.resolve()}")
    print(f"Pinned commit: {commit_hash}")
    print(f"Manifest: {manifest_path.resolve()}")
    print(f"Total files: {manifest['file_count']}")


if __name__ == "__main__":
    main()
