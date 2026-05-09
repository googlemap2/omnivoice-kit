import argparse

import soundfile as sf
import torch
from omnivoice import OmniVoice


def main():
    parser = argparse.ArgumentParser(description="Voice cloning with OmniVoice")
    parser.add_argument("--text", type=str, required=True, help="Target text")
    parser.add_argument("--ref_audio", type=str, required=True, help="Reference wav path")
    parser.add_argument("--output", type=str, default="clone_out.wav", help="Output wav path")
    parser.add_argument("--ref_text", type=str, default=None, help="Optional transcript of reference audio")
    parser.add_argument("--model", type=str, default="k2-fsa/OmniVoice", help="HF model id or local model path")
    parser.add_argument("--language", type=str, default=None, help="Language id/name, e.g. vi or Vietnamese")
    parser.add_argument("--num_step", type=int, default=16, help="Decoding steps")
    parser.add_argument("--guidance_scale", type=float, default=2.0, help="CFG scale")
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
    model = OmniVoice.from_pretrained(args.model, device_map=device, dtype=dtype)

    audio = model.generate(
        text=args.text,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        language=args.language,
        num_step=args.num_step,
        guidance_scale=args.guidance_scale,
    )[0]

    sf.write(args.output, audio, model.sampling_rate)
    print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
