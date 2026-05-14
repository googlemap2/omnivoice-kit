import argparse
import json
from pathlib import Path

import numpy as np
import torch
from omnivoice import OmniVoice
from model_store import resolve_model_source


def pick_device(device_arg: str | None) -> str:
    if device_arg:
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a reusable OmniVoice speaker prompt from reference audio."
    )
    parser.add_argument("--ref_audio", required=True, help="Reference wav path")
    parser.add_argument(
        "--ref_text",
        default=None,
        help="Optional transcript of reference audio (recommended for stable cloning)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output file path (.pt for full prompt, .npy for tokens only)",
    )
    parser.add_argument(
        "--model",
        default="k2-fsa/OmniVoice",
        help="HF model id or local model path",
    )
    parser.add_argument("--device", default=None, help="cuda | mps | cpu")
    args = parser.parse_args()

    device = pick_device(args.device)
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model_source = resolve_model_source(args.model)
    model = OmniVoice.from_pretrained(model_source, device_map=device, dtype=dtype)

    prompt = model.create_voice_clone_prompt(
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        preprocess_prompt=True,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ext = out_path.suffix.lower()
    if ext == ".pt":
        payload = {
            "ref_audio_tokens": prompt.ref_audio_tokens.detach().cpu(),
            "ref_text": prompt.ref_text,
            "ref_rms": float(prompt.ref_rms),
        }
        torch.save(payload, out_path)
        print(f"Saved prompt (.pt): {out_path}")
        return

    if ext == ".npy":
        np.save(out_path, prompt.ref_audio_tokens.detach().cpu().numpy())
        meta_path = out_path.with_suffix(".json")
        meta = {"ref_text": prompt.ref_text, "ref_rms": float(prompt.ref_rms)}
        meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")
        print(f"Saved tokens (.npy): {out_path}")
        print(f"Saved metadata (.json): {meta_path}")
        return

    raise ValueError("Unsupported output extension. Use .pt or .npy")


if __name__ == "__main__":
    main()
