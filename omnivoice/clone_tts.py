import argparse

import soundfile as sf
import torch
from omnivoice import OmniVoice
from model_store import resolve_model_source


def str2bool(value: str) -> bool:
    v = value.lower().strip()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def main():
    parser = argparse.ArgumentParser(description="Voice cloning with OmniVoice")
    parser.add_argument("--text", type=str, required=True, help="Target text")
    parser.add_argument("--ref_audio", type=str, default=None, help="Reference wav path")
    parser.add_argument("--output", type=str, default="clone_out.wav", help="Output wav path")
    parser.add_argument("--ref_text", type=str, default=None, help="Optional transcript of reference audio")
    parser.add_argument("--instruct", type=str, default=None, help="Optional voice design instruction")
    parser.add_argument("--model", type=str, default="k2-fsa/OmniVoice", help="HF model id or local model path")
    parser.add_argument("--language", type=str, default=None, help="Language id/name, e.g. vi or Vietnamese")
    parser.add_argument("--num_step", type=int, default=32, help="Decoding steps")
    parser.add_argument("--guidance_scale", type=float, default=2.0, help="CFG scale")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed factor")
    parser.add_argument("--duration", type=float, default=None, help="Fixed output duration (seconds)")
    parser.add_argument("--denoise", type=str2bool, default=True, help="Enable denoise token")
    parser.add_argument("--preprocess_prompt", type=str2bool, default=True, help="Preprocess reference prompt")
    parser.add_argument("--postprocess_output", type=str2bool, default=True, help="Trim long output silences")
    parser.add_argument("--device", type=str, default=None, help="cuda | mps | cpu")
    args = parser.parse_args()

    if args.device:
        device = args.device
    elif torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model_source = resolve_model_source(args.model)
    model = OmniVoice.from_pretrained(model_source, device_map=device, dtype=dtype)

    audio = model.generate(
        text=args.text,
        instruct=args.instruct,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        language=args.language,
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



