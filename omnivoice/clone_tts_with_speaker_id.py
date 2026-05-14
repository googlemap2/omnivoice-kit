import argparse
import json
from pathlib import Path

import soundfile as sf
import torch
from omnivoice import OmniVoice
from omnivoice.models.omnivoice import VoiceClonePrompt
from model_store import resolve_model_source


def str2bool(value: str) -> bool:
    v = value.lower().strip()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def pick_device(device_arg: str | None) -> str:
    if device_arg:
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_voice_clone_prompt(prompt_path: Path) -> VoiceClonePrompt:
    ext = prompt_path.suffix.lower()
    if ext == ".pt":
        obj = torch.load(prompt_path, map_location="cpu")
        return VoiceClonePrompt(
            ref_audio_tokens=obj["ref_audio_tokens"],
            ref_text=obj.get("ref_text", ""),
            ref_rms=float(obj.get("ref_rms", 0.1)),
        )

    if ext == ".npy":
        tokens = torch.from_numpy(__import__("numpy").load(prompt_path))
        meta_path = prompt_path.with_suffix(".json")
        meta = {"ref_text": "", "ref_rms": 0.1}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return VoiceClonePrompt(
            ref_audio_tokens=tokens,
            ref_text=meta.get("ref_text", ""),
            ref_rms=float(meta.get("ref_rms", 0.1)),
        )

    raise ValueError("Prompt file must be .pt or .npy")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voice cloning with virtual speaker_id (no fine-tune)."
    )
    parser.add_argument("--text", required=True, help="Target text")
    parser.add_argument("--speaker_id", required=True, help="Speaker id key in speakers.json")
    parser.add_argument(
        "--speakers",
        default="speakers.json",
        help="Path to speakers registry json",
    )
    parser.add_argument("--output", default="clone_out.wav", help="Output wav path")
    parser.add_argument("--model", default="k2-fsa/OmniVoice", help="Model path or HF id")
    parser.add_argument("--language", default=None, help="Language id/name, e.g. vi or en")
    parser.add_argument("--instruct", default=None, help="Optional voice design instruction")
    parser.add_argument("--num_step", type=int, default=32, help="Decoding steps")
    parser.add_argument("--guidance_scale", type=float, default=2.0, help="CFG scale")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed factor")
    parser.add_argument("--duration", type=float, default=None, help="Fixed output duration (seconds)")
    parser.add_argument("--denoise", type=str2bool, default=True, help="Enable denoise token")
    parser.add_argument("--preprocess_prompt", type=str2bool, default=True, help="Preprocess reference prompt")
    parser.add_argument("--postprocess_output", type=str2bool, default=True, help="Trim long output silences")
    parser.add_argument("--device", default=None, help="cuda | mps | cpu")
    args = parser.parse_args()

    speakers_path = Path(args.speakers)
    speakers = json.loads(speakers_path.read_text(encoding="utf-8"))
    if args.speaker_id not in speakers:
        raise KeyError(f"speaker_id '{args.speaker_id}' not found in {speakers_path}")

    cfg = speakers[args.speaker_id]
    prompt_path = Path(cfg["prompt_path"])
    voice_clone_prompt = load_voice_clone_prompt(prompt_path)

    device = pick_device(args.device)
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model_source = resolve_model_source(args.model)
    model = OmniVoice.from_pretrained(model_source, device_map=device, dtype=dtype)

    language = args.language if args.language is not None else cfg.get("language")
    audio = model.generate(
        text=args.text,
        language=language,
        voice_clone_prompt=voice_clone_prompt,
        instruct=args.instruct,
        num_step=args.num_step,
        guidance_scale=args.guidance_scale,
        speed=args.speed,
        duration=args.duration,
        denoise=args.denoise,
        preprocess_prompt=args.preprocess_prompt,
        postprocess_output=args.postprocess_output,
    )[0]

    sf.write(args.output, audio, model.sampling_rate)
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()



