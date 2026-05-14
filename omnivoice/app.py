import json
import time
from pathlib import Path

import gradio as gr
import numpy as np
import torch
from omnivoice import OmniVoice
from omnivoice.models.omnivoice import VoiceClonePrompt

from model_store import DEFAULT_MODEL_ID, resolve_model_source
from nllb.language_options import NLLB_LANGUAGE_CHOICES
from nllb.nllb_translate import DEFAULT_NLLB_MODEL_ID, translate_text
from nllb.translate_srt import translate_srt_file


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


DEVICE = pick_device()
DTYPE = torch.float16 if DEVICE in ("cuda", "mps") else torch.float32
MODEL_SOURCE = resolve_model_source(DEFAULT_MODEL_ID)
MODEL = OmniVoice.from_pretrained(MODEL_SOURCE, device_map=DEVICE, dtype=DTYPE)
SPEAKERS_PATH = Path("speakers.json")
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
    "ä¸œåŒ—è¯",
    "ä¸­å¹´",
    "ä¸­éŸ³è°ƒ",
    "äº‘å—è¯",
    "ä½ŽéŸ³è°ƒ",
    "å„¿ç«¥",
    "å››å·è¯",
    "å¥³",
    "å®å¤è¯",
    "å°‘å¹´",
    "æžä½ŽéŸ³è°ƒ",
    "æžé«˜éŸ³è°ƒ",
    "æ¡‚æž—è¯",
    "æ²³å—è¯",
    "æµŽå—è¯",
    "ç”˜è‚ƒè¯",
    "ç”·",
    "çŸ³å®¶åº„è¯",
    "è€å¹´",
    "è€³è¯­",
    "è´µå·žè¯",
    "é™•è¥¿è¯",
    "é’å²›è¯",
    "é’å¹´",
    "é«˜éŸ³è°ƒ",
]
VALID_INSTRUCTS = VALID_INSTRUCTS_EN + VALID_INSTRUCTS_ZH


def load_voice_clone_prompt(prompt_path: str) -> VoiceClonePrompt:
    path = Path(prompt_path)
    ext = path.suffix.lower()

    if ext == ".pt":
        obj = torch.load(path, map_location="cpu")
        return VoiceClonePrompt(
            ref_audio_tokens=obj["ref_audio_tokens"],
            ref_text=obj.get("ref_text", ""),
            ref_rms=float(obj.get("ref_rms", 0.1)),
        )

    if ext == ".npy":
        tokens = torch.from_numpy(np.load(path))
        meta_path = path.with_suffix(".json")
        meta = {"ref_text": "", "ref_rms": 0.1}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return VoiceClonePrompt(
            ref_audio_tokens=tokens,
            ref_text=meta.get("ref_text", ""),
            ref_rms=float(meta.get("ref_rms", 0.1)),
        )

    raise ValueError("Prompt file must be .pt or .npy")


def load_speakers():
    if not SPEAKERS_PATH.exists():
        return {}
    try:
        return json.loads(SPEAKERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_speakers(speakers):
    SPEAKERS_PATH.write_text(json.dumps(speakers, ensure_ascii=True, indent=2), encoding="utf-8")


def to_wav16(audio):
    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return MODEL.sampling_rate, wav16


def run_generate(**kwargs):
    try:
        audio = MODEL.generate(**kwargs)[0]
        return to_wav16(audio), "Done."
    except Exception as e:
        return None, f"Error: {type(e).__name__}: {e}"


def maybe_translate_text(text, enable_translate, source_lang, target_lang, nllb_model_id):
    text_clean = (text or "").strip()
    if not enable_translate:
        return text_clean, None
    translated = translate_text(
        text=text_clean,
        source_lang=(source_lang or "eng_Latn").strip(),
        target_lang=(target_lang or "vie_Latn").strip(),
        model_id=(nllb_model_id or DEFAULT_NLLB_MODEL_ID).strip(),
    )
    return translated, translated


def build_instruct_from_items(items):
    if not items:
        return None, None

    en = [x for x in items if x in VALID_INSTRUCTS_EN]
    zh = [x for x in items if x in VALID_INSTRUCTS_ZH]
    if en and zh:
        return None, "Please choose only English or only Chinese instruct items."
    if en:
        return ", ".join(en), None
    if zh:
        return "ï¼Œ".join(zh), None
    return None, "Invalid instruct items selected."


def generate_clone_with_speaker_id(
    text,
    speaker_id,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    preprocess_prompt,
    postprocess_output,
    enable_translate,
    nllb_source_lang,
    nllb_target_lang,
    nllb_model_id,
):
    if not text or not text.strip():
        return None, "Please input target text."
    if not speaker_id:
        return None, "Please choose a speaker_id."

    speakers = load_speakers()
    if speaker_id not in speakers:
        return None, f"speaker_id '{speaker_id}' not found in speakers.json."

    cfg = speakers[speaker_id]
    voice_clone_prompt = load_voice_clone_prompt(cfg["prompt_path"])
    chosen_language = language.strip() if language else cfg.get("language")
    instruct, instruct_error = build_instruct_from_items(instruct_items)
    if instruct_error:
        return None, instruct_error

    final_text, translated_text = maybe_translate_text(
        text,
        enable_translate,
        nllb_source_lang,
        nllb_target_lang,
        nllb_model_id,
    )
    kwargs = dict(
        text=final_text,
        language=chosen_language,
        voice_clone_prompt=voice_clone_prompt,
        instruct=instruct.strip() if instruct else None,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
        speed=float(speed) if speed is not None else 1.0,
        duration=float(duration) if duration else None,
        denoise=bool(denoise),
        preprocess_prompt=bool(preprocess_prompt),
        postprocess_output=bool(postprocess_output),
    )
    out_audio, status = run_generate(**kwargs)
    if translated_text:
        status = f"{status} [NLLB translated]: {translated_text}"
    return out_audio, status


def generate_clone_with_ref_audio(
    text,
    ref_audio,
    ref_text,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    preprocess_prompt,
    postprocess_output,
    enable_translate,
    nllb_source_lang,
    nllb_target_lang,
    nllb_model_id,
):
    if not text or not text.strip():
        return None, "Please input target text."
    if not ref_audio:
        return None, "Please upload reference audio."

    chosen_language = language.strip() if language else None
    instruct, instruct_error = build_instruct_from_items(instruct_items)
    if instruct_error:
        return None, instruct_error

    final_text, translated_text = maybe_translate_text(
        text,
        enable_translate,
        nllb_source_lang,
        nllb_target_lang,
        nllb_model_id,
    )
    kwargs = dict(
        text=final_text,
        ref_audio=ref_audio,
        ref_text=ref_text.strip() if ref_text else None,
        language=chosen_language,
        instruct=instruct.strip() if instruct else None,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
        speed=float(speed) if speed is not None else 1.0,
        duration=float(duration) if duration else None,
        denoise=bool(denoise),
        preprocess_prompt=bool(preprocess_prompt),
        postprocess_output=bool(postprocess_output),
    )
    out_audio, status = run_generate(**kwargs)
    if translated_text:
        status = f"{status} [NLLB translated]: {translated_text}"
    return out_audio, status


def generate_voice_design(
    text,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    postprocess_output,
    enable_translate,
    nllb_source_lang,
    nllb_target_lang,
    nllb_model_id,
):
    if not text or not text.strip():
        return None, "Please input target text."

    chosen_language = language.strip() if language else None
    instruct, instruct_error = build_instruct_from_items(instruct_items)
    if instruct_error:
        return None, instruct_error
    if not instruct:
        return None, "Please choose at least one instruct item."

    final_text, translated_text = maybe_translate_text(
        text,
        enable_translate,
        nllb_source_lang,
        nllb_target_lang,
        nllb_model_id,
    )
    kwargs = dict(
        text=final_text,
        language=chosen_language,
        instruct=instruct,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
        speed=float(speed) if speed is not None else 1.0,
        duration=float(duration) if duration else None,
        denoise=bool(denoise),
        postprocess_output=bool(postprocess_output),
    )
    out_audio, status = run_generate(**kwargs)
    if translated_text:
        status = f"{status} [NLLB translated]: {translated_text}"
    return out_audio, status


def run_translate_only(text, source_lang, target_lang, nllb_model_id):
    if not text or not text.strip():
        return "", "Please input text to translate."
    try:
        translated = translate_text(
            text=text.strip(),
            source_lang=(source_lang or "eng_Latn").strip(),
            target_lang=(target_lang or "vie_Latn").strip(),
            model_id=(nllb_model_id or DEFAULT_NLLB_MODEL_ID).strip(),
        )
        return translated, "Done."
    except Exception as e:
        return "", f"Error: {type(e).__name__}: {e}"


def run_translate_srt_file(srt_file, source_lang, target_lang, nllb_model_id, nllb_device, max_new_tokens):
    if not srt_file:
        return None, "", "", "Please upload an .srt file."
    try:
        input_path = Path(srt_file)
        out_dir = Path("assets/translated_srt")
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"{input_path.stem}.translated.{int(time.time())}.srt"
        translate_srt_file(
            input_path=input_path,
            output_path=output_path,
            source_lang=(source_lang or "eng_Latn").strip(),
            target_lang=(target_lang or "vie_Latn").strip(),
            model_id=(nllb_model_id or DEFAULT_NLLB_MODEL_ID).strip(),
            device=(nllb_device or "").strip() or None,
            max_new_tokens=int(max_new_tokens),
        )
        input_preview = input_path.read_text(encoding="utf-8", errors="replace")[:4000]
        output_preview = output_path.read_text(encoding="utf-8", errors="replace")[:4000]
        return str(output_path), input_preview, output_preview, f"Done. Saved: {output_path}"
    except Exception as e:
        return None, "", "", f"Error: {type(e).__name__}: {e}"


def get_speaker_choices():
    speakers = load_speakers()
    return [""] + sorted(speakers.keys())


def create_speaker_id(speaker_id, ref_audio, ref_text, language, save_format):
    if not speaker_id or not speaker_id.strip():
        return "Please input speaker_id."
    if not ref_audio:
        return "Please upload reference audio."

    speaker_key = speaker_id.strip()
    out_dir = Path("assets/speakers")
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = ".npy" if save_format == "npy" else ".pt"
    out_path = out_dir / f"{speaker_key}{ext}"

    try:
        prompt = MODEL.create_voice_clone_prompt(
            ref_audio=ref_audio,
            ref_text=ref_text.strip() if ref_text else None,
            preprocess_prompt=True,
        )
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    try:
        if ext == ".pt":
            payload = {
                "ref_audio_tokens": prompt.ref_audio_tokens.detach().cpu(),
                "ref_text": prompt.ref_text,
                "ref_rms": float(prompt.ref_rms),
            }
            torch.save(payload, out_path)
        else:
            np.save(out_path, prompt.ref_audio_tokens.detach().cpu().numpy())
            meta_path = out_path.with_suffix(".json")
            meta = {"ref_text": prompt.ref_text, "ref_rms": float(prompt.ref_rms)}
            meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

        speakers = load_speakers()
        speakers[speaker_key] = {
            "prompt_path": str(out_path).replace("\\", "/"),
            "language": language.strip() if language else None,
        }
        save_speakers(speakers)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    return f"Created speaker_id '{speaker_key}' at {out_path}."


def delete_speaker_id(speaker_id):
    if not speaker_id:
        return "Please choose a speaker_id to delete."

    speakers = load_speakers()
    if speaker_id not in speakers:
        return f"speaker_id '{speaker_id}' not found."

    cfg = speakers[speaker_id]
    prompt_path = Path(cfg.get("prompt_path", ""))
    deleted_files = []
    try:
        if prompt_path.exists():
            prompt_path.unlink()
            deleted_files.append(str(prompt_path))
        if prompt_path.suffix.lower() == ".npy":
            meta_path = prompt_path.with_suffix(".json")
            if meta_path.exists():
                meta_path.unlink()
                deleted_files.append(str(meta_path))
    except Exception as e:
        return f"Error while deleting files: {type(e).__name__}: {e}"

    del speakers[speaker_id]
    save_speakers(speakers)
    if deleted_files:
        return f"Deleted speaker_id '{speaker_id}' and files: {', '.join(deleted_files)}"
    return f"Deleted speaker_id '{speaker_id}' from speakers.json."


def rename_speaker_id(old_speaker_id, new_speaker_id):
    if not old_speaker_id:
        return "Please choose a speaker_id to rename."
    if not new_speaker_id or not new_speaker_id.strip():
        return "Please input new speaker_id."

    new_key = new_speaker_id.strip()
    speakers = load_speakers()
    if old_speaker_id not in speakers:
        return f"speaker_id '{old_speaker_id}' not found."
    if new_key in speakers and new_key != old_speaker_id:
        return f"speaker_id '{new_key}' already exists."
    if new_key == old_speaker_id:
        return "New speaker_id is the same as current speaker_id."

    cfg = speakers[old_speaker_id]
    old_prompt_path = Path(cfg.get("prompt_path", ""))
    new_prompt_path = old_prompt_path

    try:
        if old_prompt_path.exists():
            new_prompt_path = old_prompt_path.with_name(f"{new_key}{old_prompt_path.suffix}")
            old_prompt_path.rename(new_prompt_path)
            if old_prompt_path.suffix.lower() == ".npy":
                old_meta = old_prompt_path.with_suffix(".json")
                new_meta = new_prompt_path.with_suffix(".json")
                if old_meta.exists():
                    old_meta.rename(new_meta)
    except Exception as e:
        return f"Error while renaming files: {type(e).__name__}: {e}"

    speakers[new_key] = dict(cfg)
    speakers[new_key]["prompt_path"] = str(new_prompt_path).replace("\\", "/")
    del speakers[old_speaker_id]
    save_speakers(speakers)
    return f"Renamed speaker_id '{old_speaker_id}' to '{new_key}'."


with gr.Blocks(title="OmniVoice Voice Clone Kit") as demo:
    gr.Markdown("# OmniVoice Voice Clone Kit")
    gr.Markdown("Choose one mode: clone from `speaker_id` or clone from uploaded reference audio.")

    with gr.Tabs():
        with gr.Tab("TTS by Speaker ID"):
            with gr.Row():
                with gr.Column():
                    sid_text = gr.Textbox(label="Target Text", lines=4)
                    sid_speaker_id = gr.Dropdown(
                        choices=get_speaker_choices(),
                        value="",
                        label="Speaker ID (from speakers.json)",
                        allow_custom_value=False,
                    )
                    sid_language = gr.Textbox(
                        label="Language (optional, e.g. vi, en, Vietnamese)",
                        lines=1,
                    )
                    sid_instruct_items = gr.CheckboxGroup(
                        choices=VALID_INSTRUCTS,
                        label="Instruct (optional, choose valid items only)",
                    )
                    sid_num_step = gr.Slider(4, 64, value=16, step=1, label="Inference Steps")
                    sid_guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
                    sid_speed = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="Speed")
                    sid_duration = gr.Number(value=None, label="Duration (seconds, optional)")
                    sid_denoise = gr.Checkbox(value=True, label="Denoise")
                    sid_preprocess_prompt = gr.Checkbox(value=True, label="Preprocess Prompt")
                    sid_postprocess_output = gr.Checkbox(value=True, label="Postprocess Output")
                    sid_enable_translate = gr.Checkbox(value=False, label="Translate text with NLLB before TTS")
                    sid_nllb_source = gr.Textbox(label="NLLB Source Lang (e.g. eng_Latn)", value="eng_Latn", lines=1)
                    sid_nllb_target = gr.Textbox(label="NLLB Target Lang (e.g. vie_Latn)", value="vie_Latn", lines=1)
                    sid_nllb_model = gr.Textbox(label="NLLB Model ID", value=DEFAULT_NLLB_MODEL_ID, lines=1)
                    sid_run = gr.Button("Generate", variant="primary")
                    sid_refresh = gr.Button("Refresh Speaker IDs")
                with gr.Column():
                    sid_out_audio = gr.Audio(type="numpy", label="Output")
                    sid_status = gr.Textbox(label="Status")

            sid_run.click(
                fn=generate_clone_with_speaker_id,
                inputs=[
                    sid_text,
                    sid_speaker_id,
                    sid_language,
                    sid_instruct_items,
                    sid_num_step,
                    sid_guidance_scale,
                    sid_speed,
                    sid_duration,
                    sid_denoise,
                    sid_preprocess_prompt,
                    sid_postprocess_output,
                    sid_enable_translate,
                    sid_nllb_source,
                    sid_nllb_target,
                    sid_nllb_model,
                ],
                outputs=[sid_out_audio, sid_status],
            )
            sid_refresh.click(
                fn=lambda: gr.Dropdown(choices=get_speaker_choices(), value=""),
                inputs=[],
                outputs=[sid_speaker_id],
            )

        with gr.Tab("Clone by Reference Audio"):
            with gr.Row():
                with gr.Column():
                    ref_text_target = gr.Textbox(label="Target Text", lines=4)
                    ref_audio = gr.Audio(type="filepath", label="Reference Audio")
                    ref_text = gr.Textbox(label="Reference Transcript (optional)", lines=2)
                    ref_language = gr.Textbox(
                        label="Language (optional, e.g. vi, en, Vietnamese)",
                        lines=1,
                    )
                    ref_instruct_items = gr.CheckboxGroup(
                        choices=VALID_INSTRUCTS,
                        label="Instruct (optional, choose valid items only)",
                    )
                    ref_num_step = gr.Slider(4, 64, value=16, step=1, label="Inference Steps")
                    ref_guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
                    ref_speed = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="Speed")
                    ref_duration = gr.Number(value=None, label="Duration (seconds, optional)")
                    ref_denoise = gr.Checkbox(value=True, label="Denoise")
                    ref_preprocess_prompt = gr.Checkbox(value=True, label="Preprocess Prompt")
                    ref_postprocess_output = gr.Checkbox(value=True, label="Postprocess Output")
                    ref_enable_translate = gr.Checkbox(value=False, label="Translate text with NLLB before TTS")
                    ref_nllb_source = gr.Textbox(label="NLLB Source Lang (e.g. eng_Latn)", value="eng_Latn", lines=1)
                    ref_nllb_target = gr.Textbox(label="NLLB Target Lang (e.g. vie_Latn)", value="vie_Latn", lines=1)
                    ref_nllb_model = gr.Textbox(label="NLLB Model ID", value=DEFAULT_NLLB_MODEL_ID, lines=1)
                    ref_run = gr.Button("Generate", variant="primary")
                with gr.Column():
                    ref_out_audio = gr.Audio(type="numpy", label="Output")
                    ref_status = gr.Textbox(label="Status")

            ref_run.click(
                fn=generate_clone_with_ref_audio,
                inputs=[
                    ref_text_target,
                    ref_audio,
                    ref_text,
                    ref_language,
                    ref_instruct_items,
                    ref_num_step,
                    ref_guidance_scale,
                    ref_speed,
                    ref_duration,
                    ref_denoise,
                    ref_preprocess_prompt,
                    ref_postprocess_output,
                    ref_enable_translate,
                    ref_nllb_source,
                    ref_nllb_target,
                    ref_nllb_model,
                ],
                outputs=[ref_out_audio, ref_status],
            )

        with gr.Tab("Voice Design"):
            with gr.Row():
                with gr.Column():
                    vd_text = gr.Textbox(label="Target Text", lines=4)
                    vd_language = gr.Textbox(
                        label="Language (optional, e.g. vi, en, Vietnamese)",
                        lines=1,
                    )
                    vd_instruct_items = gr.CheckboxGroup(
                        choices=VALID_INSTRUCTS,
                        label="Instruct (required, choose valid items only)",
                    )
                    vd_num_step = gr.Slider(4, 64, value=16, step=1, label="Inference Steps")
                    vd_guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
                    vd_speed = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="Speed")
                    vd_duration = gr.Number(value=None, label="Duration (seconds, optional)")
                    vd_denoise = gr.Checkbox(value=True, label="Denoise")
                    vd_postprocess_output = gr.Checkbox(value=True, label="Postprocess Output")
                    vd_enable_translate = gr.Checkbox(value=False, label="Translate text with NLLB before TTS")
                    vd_nllb_source = gr.Textbox(label="NLLB Source Lang (e.g. eng_Latn)", value="eng_Latn", lines=1)
                    vd_nllb_target = gr.Textbox(label="NLLB Target Lang (e.g. vie_Latn)", value="vie_Latn", lines=1)
                    vd_nllb_model = gr.Textbox(label="NLLB Model ID", value=DEFAULT_NLLB_MODEL_ID, lines=1)
                    vd_run = gr.Button("Generate", variant="primary")
                with gr.Column():
                    vd_out_audio = gr.Audio(type="numpy", label="Output")
                    vd_status = gr.Textbox(label="Status")

            vd_run.click(
                fn=generate_voice_design,
                inputs=[
                    vd_text,
                    vd_language,
                    vd_instruct_items,
                    vd_num_step,
                    vd_guidance_scale,
                    vd_speed,
                    vd_duration,
                    vd_denoise,
                    vd_postprocess_output,
                    vd_enable_translate,
                    vd_nllb_source,
                    vd_nllb_target,
                    vd_nllb_model,
                ],
                outputs=[vd_out_audio, vd_status],
            )

        with gr.Tab("Translate (NLLB)"):
            with gr.Row():
                with gr.Column():
                    tr_input = gr.Textbox(label="Input Text", lines=6)
                    tr_source = gr.Dropdown(
                        choices=NLLB_LANGUAGE_CHOICES,
                        value="eng_Latn",
                        label="Source Lang Code",
                        allow_custom_value=True,
                    )
                    tr_target = gr.Dropdown(
                        choices=NLLB_LANGUAGE_CHOICES,
                        value="vie_Latn",
                        label="Target Lang Code",
                        allow_custom_value=True,
                    )
                    tr_model = gr.Textbox(label="NLLB Model ID", value=DEFAULT_NLLB_MODEL_ID, lines=1)
                    tr_run = gr.Button("Translate", variant="primary")
                with gr.Column():
                    tr_output = gr.Textbox(label="Translated Text", lines=6)
                    tr_status = gr.Textbox(label="Status")

            tr_run.click(
                fn=run_translate_only,
                inputs=[tr_input, tr_source, tr_target, tr_model],
                outputs=[tr_output, tr_status],
            )

        with gr.Tab("Translate SRT (NLLB)"):
            with gr.Row():
                with gr.Column():
                    srt_input = gr.File(label="Input .srt File", file_types=[".srt"], type="filepath")
                    srt_source = gr.Dropdown(
                        choices=NLLB_LANGUAGE_CHOICES,
                        value="eng_Latn",
                        label="Source Lang Code",
                        allow_custom_value=True,
                    )
                    srt_target = gr.Dropdown(
                        choices=NLLB_LANGUAGE_CHOICES,
                        value="vie_Latn",
                        label="Target Lang Code",
                        allow_custom_value=True,
                    )
                    srt_model = gr.Textbox(label="NLLB Model ID", value=DEFAULT_NLLB_MODEL_ID, lines=1)
                    srt_device = gr.Dropdown(
                        choices=["", "cuda", "mps", "cpu"],
                        value="",
                        label="NLLB Device (optional)",
                        allow_custom_value=False,
                    )
                    srt_max_new_tokens = gr.Slider(16, 1024, value=256, step=16, label="Max New Tokens per Line")
                    srt_run = gr.Button("Translate SRT", variant="primary")
                with gr.Column():
                    srt_output = gr.File(label="Translated .srt File")
                    srt_input_preview = gr.Textbox(label="Input Preview", lines=12)
                    srt_output_preview = gr.Textbox(label="Translated Preview", lines=12)
                    srt_status = gr.Textbox(label="Status")

            srt_run.click(
                fn=run_translate_srt_file,
                inputs=[srt_input, srt_source, srt_target, srt_model, srt_device, srt_max_new_tokens],
                outputs=[srt_output, srt_input_preview, srt_output_preview, srt_status],
            )

        with gr.Tab("Create Speaker ID"):
            with gr.Tabs():
                with gr.Tab("Create"):
                    with gr.Row():
                        with gr.Column():
                            cs_speaker_id = gr.Textbox(label="Speaker ID", lines=1)
                            cs_ref_audio = gr.Audio(type="filepath", label="Reference Audio")
                            cs_ref_text = gr.Textbox(label="Reference Transcript (optional)", lines=2)
                            cs_language = gr.Textbox(label="Language (optional, e.g. vi, en)", lines=1)
                            cs_save_format = gr.Radio(
                                choices=["pt", "npy"],
                                value="pt",
                                label="Prompt Save Format",
                            )
                            cs_create = gr.Button("Create", variant="primary")
                        with gr.Column():
                            cs_status = gr.Textbox(label="Status", lines=4)

                    cs_create.click(
                        fn=create_speaker_id,
                        inputs=[cs_speaker_id, cs_ref_audio, cs_ref_text, cs_language, cs_save_format],
                        outputs=[cs_status],
                    )

                with gr.Tab("Edit"):
                    with gr.Row():
                        with gr.Column():
                            ce_selected = gr.Dropdown(
                                choices=get_speaker_choices(),
                                value="",
                                label="Existing Speaker ID",
                                allow_custom_value=False,
                            )
                            ce_refresh = gr.Button("Refresh List")
                        with gr.Column():
                            ce_new_name = gr.Textbox(label="New Speaker ID Name", lines=1)
                            ce_rename = gr.Button("Rename Selected")
                            ce_status = gr.Textbox(label="Edit Status", lines=4)

                    ce_refresh.click(
                        fn=lambda: gr.Dropdown(choices=get_speaker_choices(), value=""),
                        inputs=[],
                        outputs=[ce_selected],
                    )
                    ce_rename.click(
                        fn=rename_speaker_id,
                        inputs=[ce_selected, ce_new_name],
                        outputs=[ce_status],
                    )

                with gr.Tab("Delete"):
                    with gr.Row():
                        with gr.Column():
                            cd_selected = gr.Dropdown(
                                choices=get_speaker_choices(),
                                value="",
                                label="Existing Speaker ID",
                                allow_custom_value=False,
                            )
                            cd_refresh = gr.Button("Refresh List")
                        with gr.Column():
                            cd_delete = gr.Button("Delete Selected", variant="stop")
                            cd_status = gr.Textbox(label="Delete Status", lines=4)

                    cd_refresh.click(
                        fn=lambda: gr.Dropdown(choices=get_speaker_choices(), value=""),
                        inputs=[],
                        outputs=[cd_selected],
                    )
                    cd_delete.click(
                        fn=delete_speaker_id,
                        inputs=[cd_selected],
                        outputs=[cd_status],
                    )


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7861)





