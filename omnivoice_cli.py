import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from model_store import DEFAULT_MODEL_ID, resolve_model_source


VALID_INSTRUCTS_EN = [
    "american accent",
    "australian accent",
    "british accent",
    "canadian accent",
    "child",
    "chinese accent",
    "elderly",
    "female",
    "high pitch",
    "indian accent",
    "japanese accent",
    "korean accent",
    "low pitch",
    "male",
    "middle-aged",
    "moderate pitch",
    "portuguese accent",
    "russian accent",
    "teenager",
    "very high pitch",
    "very low pitch",
    "whisper",
    "young adult",
]
VALID_INSTRUCTS_ZH = [
    "东北话",
    "中年",
    "中音调",
    "云南话",
    "低音调",
    "儿童",
    "四川话",
    "女",
    "宁夏话",
    "少年",
    "极低音调",
    "极高音调",
    "桂林话",
    "河南话",
    "济南话",
    "甘肃话",
    "男",
    "石家庄话",
    "老年",
    "耳语",
    "贵州话",
    "陕西话",
    "青岛话",
    "青年",
    "高音调",
]


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


def load_model(model_arg: str, device_arg: str | None):
    from omnivoice import OmniVoice

    device = pick_device(device_arg)
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model_source = resolve_model_source(model_arg)
    return OmniVoice.from_pretrained(model_source, device_map=device, dtype=dtype)


def build_instruct(instruct_items: list[str] | None, required: bool = False) -> str | None:
    if not instruct_items:
        if required:
            raise ValueError("Please provide at least one --instruct-item.")
        return None

    en = [x for x in instruct_items if x in VALID_INSTRUCTS_EN]
    zh = [x for x in instruct_items if x in VALID_INSTRUCTS_ZH]
    if en and zh:
        raise ValueError("Please choose only English or only Chinese instruct items.")
    if not en and not zh:
        raise ValueError("Invalid instruct items.")
    if len(en) != len(instruct_items) and len(zh) != len(instruct_items):
        raise ValueError("Some instruct items are invalid.")
    if en:
        return ", ".join(en)
    return "，".join(zh)


def load_voice_clone_prompt(prompt_path: Path):
    from omnivoice.models.omnivoice import VoiceClonePrompt

    ext = prompt_path.suffix.lower()
    if ext == ".pt":
        obj = torch.load(prompt_path, map_location="cpu")
        return VoiceClonePrompt(
            ref_audio_tokens=obj["ref_audio_tokens"],
            ref_text=obj.get("ref_text", ""),
            ref_rms=float(obj.get("ref_rms", 0.1)),
        )
    if ext == ".npy":
        tokens = torch.from_numpy(np.load(prompt_path))
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


def run_speaker_id(args: argparse.Namespace) -> None:
    speakers = json.loads(Path(args.speakers).read_text(encoding="utf-8"))
    if args.speaker_id not in speakers:
        raise KeyError(f"speaker_id '{args.speaker_id}' not found in {args.speakers}")

    cfg = speakers[args.speaker_id]
    voice_clone_prompt = load_voice_clone_prompt(Path(cfg["prompt_path"]))
    language = args.language if args.language is not None else cfg.get("language")
    instruct = build_instruct(args.instruct_item, required=False)

    model = load_model(args.model, args.device)
    audio = model.generate(
        text=args.text.strip(),
        language=language,
        voice_clone_prompt=voice_clone_prompt,
        instruct=instruct,
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


def run_ref_audio(args: argparse.Namespace) -> None:
    instruct = build_instruct(args.instruct_item, required=False)
    language = args.language if args.language is not None else None

    model = load_model(args.model, args.device)
    audio = model.generate(
        text=args.text.strip(),
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        language=language,
        instruct=instruct,
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


def run_voice_design(args: argparse.Namespace) -> None:
    instruct = build_instruct(args.instruct_item, required=True)
    language = args.language if args.language is not None else None

    model = load_model(args.model, args.device)
    audio = model.generate(
        text=args.text.strip(),
        language=language,
        instruct=instruct,
        num_step=args.num_step,
        guidance_scale=args.guidance_scale,
        speed=args.speed,
        duration=args.duration,
        denoise=args.denoise,
        postprocess_output=args.postprocess_output,
    )[0]
    sf.write(args.output, audio, model.sampling_rate)
    print(f"Saved to: {args.output}")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", required=True, help="Target text")
    parser.add_argument("--output", default="out.wav", help="Output wav path")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, help="HF model id or local model path")
    parser.add_argument("--language", default=None, help="Language id/name, e.g. vi or en")
    parser.add_argument(
        "--instruct-item",
        action="append",
        default=[],
        help="Instruct item from UI list. Use multiple times for multiple items.",
    )
    parser.add_argument("--num_step", type=int, default=16, help="Decoding steps")
    parser.add_argument("--guidance_scale", type=float, default=2.0, help="CFG scale")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed factor")
    parser.add_argument("--duration", type=float, default=None, help="Fixed output duration (seconds)")
    parser.add_argument("--denoise", type=str2bool, default=True, help="Enable denoise token")
    parser.add_argument("--postprocess_output", type=str2bool, default=True, help="Trim long output silences")
    parser.add_argument("--device", default=None, help="cuda | mps | cpu")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI for OmniVoice modes without Web UI."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    speaker_id = subparsers.add_parser("speaker-id", help="TTS by Speaker ID")
    add_common_args(speaker_id)
    speaker_id.add_argument("--speaker_id", required=True, help="speaker_id key in speakers.json")
    speaker_id.add_argument("--speakers", default="speakers.json", help="Path to speakers registry json")
    speaker_id.add_argument("--preprocess_prompt", type=str2bool, default=True, help="Preprocess reference prompt")
    speaker_id.set_defaults(func=run_speaker_id)

    ref_audio = subparsers.add_parser("ref-audio", help="Clone by Reference Audio")
    add_common_args(ref_audio)
    ref_audio.add_argument("--ref_audio", required=True, help="Reference wav path")
    ref_audio.add_argument("--ref_text", default=None, help="Optional transcript of reference audio")
    ref_audio.add_argument("--preprocess_prompt", type=str2bool, default=True, help="Preprocess reference prompt")
    ref_audio.set_defaults(func=run_ref_audio)

    voice_design = subparsers.add_parser("voice-design", help="Voice Design")
    add_common_args(voice_design)
    voice_design.set_defaults(func=run_voice_design)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
