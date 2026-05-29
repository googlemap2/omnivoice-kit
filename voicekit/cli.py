import argparse
import json
from pathlib import Path

import soundfile as sf

from voicekit.audio import EFFECT_PRESETS, apply_effect_preset
from voicekit.asr import (
    DEFAULT_ASR_MODEL_ID,
    TRANSCRIPTION_FORMATS,
    format_transcription,
    transcribe_file,
)
from voicekit.core import (
    build_instruct,
    get_profile_store,
    load_model,
    load_voice_clone_prompt,
)
from voicekit.dubbing import dub_file
from voicekit.history import try_record_generation
from voicekit.model_store import DEFAULT_MODEL_ID
from voicekit.settings import load_settings
from voicekit.subtitles import SUBTITLE_FORMATS, export_subtitle, parse_subtitle_file
from voicekit.translation import list_providers, translate_segments, translate_text


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
    audio = apply_effect_preset(audio, args.effect_preset)
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
            "effect_preset": args.effect_preset,
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
    audio = apply_effect_preset(audio, args.effect_preset)
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
            "effect_preset": args.effect_preset,
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
    audio = apply_effect_preset(audio, args.effect_preset)
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
            "effect_preset": args.effect_preset,
        },
    )
    print(f"Saved to: {args.output}")


def run_translate(args: argparse.Namespace) -> None:
    if args.segments_json:
        segments_path = Path(args.segments_json)
        raw = json.loads(segments_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            segments_payload = raw.get("segments", raw)
        else:
            segments_payload = raw
        result = translate_segments(
            segments=segments_payload,
            source_language=args.source_language,
            target_language=args.target_language,
            provider_id=args.provider,
        )
    else:
        if not args.text or not args.text.strip():
            raise ValueError("Provide --text or --segments-json.")
        result = translate_text(
            text=args.text,
            source_language=args.source_language,
            target_language=args.target_language,
            provider_id=args.provider,
        )

    output = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}")
    else:
        print(output)


def run_subtitle_import(args: argparse.Namespace) -> None:
    segments = parse_subtitle_file(args.input, args.format)
    output = json.dumps(
        {"segments": [segment.to_dict() for segment in segments]},
        ensure_ascii=False,
        indent=2,
    )
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}")
    else:
        print(output)


def run_subtitle_export(args: argparse.Namespace) -> None:
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    segments = raw.get("segments", raw) if isinstance(raw, dict) else raw
    if not isinstance(segments, list):
        raise ValueError("Input JSON must be a segments array or {segments: [...]} object.")
    output = export_subtitle(segments, args.format)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}")
    else:
        print(output)


def run_dub(args: argparse.Namespace) -> None:
    result = dub_file(
        input_path=args.input,
        voice=args.voice,
        target_language=args.target_language,
        source_language=args.source_language,
        translation_provider=args.provider,
        output_dir=args.output_dir,
        tts_model=args.tts_model,
        asr_model=args.asr_model,
        effect_preset=args.effect_preset,
        num_step=args.num_step,
        guidance_scale=args.guidance_scale,
        speed=args.speed,
        device=args.device,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


def run_transcribe(args: argparse.Namespace) -> None:
    result = transcribe_file(
        audio_path=args.input,
        model_id=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        word_timestamps=args.word_timestamps,
        beam_size=args.beam_size,
    )
    formatted = format_transcription(result, args.format)
    if isinstance(formatted, dict):
        import json

        output = json.dumps(formatted, ensure_ascii=False, indent=2)
    else:
        output = formatted

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}")
    else:
        print(output)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    settings = load_settings()
    parser.add_argument("--text", required=True, help="Target text")
    parser.add_argument("--output", default="out.wav", help="Output wav path")
    parser.add_argument("--model", default=settings.default_model, help="HF model id or local model path")
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
    parser.add_argument(
        "--effect-preset",
        choices=EFFECT_PRESETS,
        default=settings.default_effect_preset,
        help="Audio effect preset",
    )
    parser.add_argument("--device", default=settings.default_device, help="cuda | mps | cpu")


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

    transcribe = subparsers.add_parser("transcribe", help="Transcribe audio with faster-whisper")
    transcribe.add_argument("--input", required=True, help="Input audio/video path")
    transcribe.add_argument("--output", default=None, help="Optional output text/json/srt/vtt path")
    transcribe.add_argument("--model", default=DEFAULT_ASR_MODEL_ID, help="ASR model id or local model path")
    transcribe.add_argument("--language", default=None, help="Optional source language, e.g. vi or en")
    transcribe.add_argument("--device", default=None, help="cuda | mps | cpu")
    transcribe.add_argument("--compute-type", default=None, help="faster-whisper compute type, e.g. int8 or float16")
    transcribe.add_argument("--word-timestamps", type=str2bool, default=False, help="Return word timestamps")
    transcribe.add_argument("--beam-size", type=int, default=5, help="Beam size")
    transcribe.add_argument("--format", choices=TRANSCRIPTION_FORMATS, default="text", help="Output format")
    transcribe.set_defaults(func=run_transcribe)

    translate = subparsers.add_parser("translate", help="Translate text or subtitle segments")
    settings = load_settings()
    provider_choices = [provider.id for provider in list_providers(settings)]
    translate.add_argument("--text", default=None, help="Text to translate")
    translate.add_argument(
        "--segments-json",
        default=None,
        help="JSON file with segments array or {segments: [...]}",
    )
    translate.add_argument("--source-language", default=None, help="Source language code, e.g. vi or en")
    translate.add_argument("--target-language", default=None, help="Target language code, e.g. en or vi")
    translate.add_argument(
        "--provider",
        default=settings.default_translation_provider,
        choices=provider_choices,
        help="Translation provider id",
    )
    translate.add_argument("--output", default=None, help="Optional output JSON path")
    translate.set_defaults(func=run_translate)

    subtitle_import = subparsers.add_parser("subtitle-import", help="Import SRT/VTT to JSON segments")
    subtitle_import.add_argument("--input", required=True, help="Input .srt or .vtt path")
    subtitle_import.add_argument("--output", default=None, help="Optional output JSON path")
    subtitle_import.add_argument(
        "--format",
        choices=SUBTITLE_FORMATS,
        default=None,
        help="Subtitle format; defaults to input file extension",
    )
    subtitle_import.set_defaults(func=run_subtitle_import)

    subtitle_export = subparsers.add_parser("subtitle-export", help="Export JSON segments to SRT/VTT")
    subtitle_export.add_argument("--input", required=True, help="Input JSON segments path")
    subtitle_export.add_argument("--output", default=None, help="Optional subtitle output path")
    subtitle_export.add_argument("--format", choices=SUBTITLE_FORMATS, default="srt", help="Output subtitle format")
    subtitle_export.set_defaults(func=run_subtitle_export)

    dub = subparsers.add_parser("dub", help="Dub an audio/video file with ASR, translation, and TTS")
    dub.add_argument("--input", required=True, help="Input audio/video path")
    dub.add_argument("--voice", required=True, help="Voice profile id used for all segments in v1")
    dub.add_argument("--target-language", required=True, help="Target language code, e.g. vi or en")
    dub.add_argument("--source-language", default=None, help="Optional source language code")
    dub.add_argument("--provider", default=settings.default_translation_provider, help="Translation provider id")
    dub.add_argument("--output-dir", default="outputs/dubbing", help="Output directory")
    dub.add_argument("--tts-model", default=settings.default_model, help="TTS model id or local path")
    dub.add_argument("--asr-model", default=DEFAULT_ASR_MODEL_ID, help="ASR model id or local path")
    dub.add_argument("--effect-preset", choices=EFFECT_PRESETS, default=settings.default_effect_preset)
    dub.add_argument("--num_step", type=int, default=16)
    dub.add_argument("--guidance_scale", type=float, default=2.0)
    dub.add_argument("--speed", type=float, default=1.0)
    dub.add_argument("--device", default=settings.default_device, help="cuda | mps | cpu")
    dub.set_defaults(func=run_dub)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
