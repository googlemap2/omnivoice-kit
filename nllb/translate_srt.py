from __future__ import annotations

import argparse
import re
from pathlib import Path

from nllb.nllb_translate import DEFAULT_NLLB_MODEL_ID, translate_text


TIMECODE_RE = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _translate_block_lines(
    lines: list[str],
    source_lang: str,
    target_lang: str,
    model_id: str,
    device: str | None,
    max_new_tokens: int,
) -> list[str]:
    if len(lines) < 2 or not TIMECODE_RE.match(lines[1].strip()):
        return lines

    translated = lines[:2]
    for text_line in lines[2:]:
        if text_line.strip():
            translated.append(
                translate_text(
                    text=text_line,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model_id=model_id,
                    device=device,
                    max_new_tokens=max_new_tokens,
                )
            )
        else:
            translated.append(text_line)
    return translated


def translate_srt_file(
    input_path: Path,
    output_path: Path,
    source_lang: str,
    target_lang: str,
    model_id: str,
    device: str | None,
    max_new_tokens: int,
) -> None:
    raw = _read_text(input_path)
    blocks = re.split(r"\r?\n\r?\n", raw.strip())
    out_blocks: list[str] = []

    for idx, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        translated_lines = _translate_block_lines(
            lines=lines,
            source_lang=source_lang,
            target_lang=target_lang,
            model_id=model_id,
            device=device,
            max_new_tokens=max_new_tokens,
        )
        out_blocks.append("\n".join(translated_lines))
        if idx % 20 == 0:
            print(f"Translated {idx}/{len(blocks)} subtitle blocks...")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(out_blocks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate .srt subtitles with NLLB.")
    parser.add_argument("--input", required=True, help="Input .srt path")
    parser.add_argument("--output", required=True, help="Output .srt path")
    parser.add_argument("--source-lang", default="eng_Latn", help="NLLB source language code")
    parser.add_argument("--target-lang", default="vie_Latn", help="NLLB target language code")
    parser.add_argument("--model-id", default=DEFAULT_NLLB_MODEL_ID, help="NLLB model id or local path")
    parser.add_argument("--device", default=None, help="cuda | mps | cpu")
    parser.add_argument("--max-new-tokens", type=int, default=256, help="Max tokens per subtitle line")
    args = parser.parse_args()

    translate_srt_file(
        input_path=Path(args.input),
        output_path=Path(args.output),
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        model_id=args.model_id,
        device=args.device,
        max_new_tokens=args.max_new_tokens,
    )
    print(f"Done. Saved translated subtitle to: {args.output}")


if __name__ == "__main__":
    main()

