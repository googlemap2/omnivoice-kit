import argparse
from pathlib import Path

import soundfile as sf

from voicekit.core import (
    build_instruct,
    get_profile_store,
    load_model,
    load_voice_clone_prompt,
)
from voicekit.history import try_record_generation
from voicekit.model_store import DEFAULT_MODEL_ID


def str2bool(value: str) -> bool:
    v = value.lower().strip()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def run_speaker_id(args: argparse.Namespace) -> None:
    profile = get_profile_store(args.speakers).get_profile(args.speaker_id)
    if profile is None:
        raise KeyError(f"speaker_id '{args.speaker_id}' not found in {args.speakers}")

    voice_clone_prompt = load_voice_clone_prompt(Path(profile.prompt_path))
    language = args.language if args.language is not None else profile.language
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
    try_record_generation(
        mode="speaker-id",
        model=args.model,
        text=args.text.strip(),
        voice=args.speaker_id,
        language=language,
        output_path=args.output,
        params={
            "instruct_items": args.instruct_item,
            "num_step": args.num_step,
            "guidance_scale": args.guidance_scale,
            "speed": args.speed,
            "duration": args.duration,
            "denoise": args.denoise,
            "preprocess_prompt": args.preprocess_prompt,
            "postprocess_output": args.postprocess_output,
            "device": args.device,
        },
    )
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
    try_record_generation(
        mode="ref-audio",
        model=args.model,
        text=args.text.strip(),
        voice=args.ref_audio,
        language=language,
        output_path=args.output,
        params={
            "ref_text": args.ref_text,
            "instruct_items": args.instruct_item,
            "num_step": args.num_step,
            "guidance_scale": args.guidance_scale,
            "speed": args.speed,
            "duration": args.duration,
            "denoise": args.denoise,
            "preprocess_prompt": args.preprocess_prompt,
            "postprocess_output": args.postprocess_output,
            "device": args.device,
        },
    )
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
    try_record_generation(
        mode="voice-design",
        model=args.model,
        text=args.text.strip(),
        voice=None,
        language=language,
        output_path=args.output,
        params={
            "instruct_items": args.instruct_item,
            "num_step": args.num_step,
            "guidance_scale": args.guidance_scale,
            "speed": args.speed,
            "duration": args.duration,
            "denoise": args.denoise,
            "postprocess_output": args.postprocess_output,
            "device": args.device,
        },
    )
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
    parser = argparse.ArgumentParser(description="CLI for OmniVoice modes without Web UI.")
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
