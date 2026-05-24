import json
from pathlib import Path

import numpy as np
import torch
from omnivoice import OmniVoice
from omnivoice.models.omnivoice import VoiceClonePrompt

from model_store import DEFAULT_MODEL_ID, resolve_model_source


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
    "\u4e1c\u5317\u8bdd",
    "\u4e2d\u5e74",
    "\u4e2d\u97f3\u8c03",
    "\u4e91\u5357\u8bdd",
    "\u4f4e\u97f3\u8c03",
    "\u513f\u7ae5",
    "\u56db\u5ddd\u8bdd",
    "\u5973",
    "\u5b81\u590f\u8bdd",
    "\u5c11\u5e74",
    "\u6781\u4f4e\u97f3\u8c03",
    "\u6781\u9ad8\u97f3\u8c03",
    "\u6842\u6797\u8bdd",
    "\u6cb3\u5357\u8bdd",
    "\u6d4e\u5357\u8bdd",
    "\u7518\u8083\u8bdd",
    "\u7537",
    "\u77f3\u5bb6\u5e84\u8bdd",
    "\u8001\u5e74",
    "\u8033\u8bed",
    "\u8d35\u5dde\u8bdd",
    "\u9655\u897f\u8bdd",
    "\u9752\u5c9b\u8bdd",
    "\u9752\u5e74",
    "\u9ad8\u97f3\u8c03",
]
VALID_INSTRUCTS = VALID_INSTRUCTS_EN + VALID_INSTRUCTS_ZH
OMNIVOICE_LANGUAGE_CHOICES = [
    ("Vietnamese (vi)", "vi"),
    ("English (en)", "en"),
    ("Chinese (zh)", "zh"),
    ("Japanese (ja)", "ja"),
    ("Korean (ko)", "ko"),
    ("French (fr)", "fr"),
    ("German (de)", "de"),
    ("Spanish (es)", "es"),
    ("Russian (ru)", "ru"),
    ("Thai (th)", "th"),
    ("Indonesian (id)", "id"),
]
OMNIVOICE_MODEL_CHOICES = [
    ("OmniVoice Original (k2-fsa/OmniVoice)", "k2-fsa/OmniVoice"),
]


def pick_device(device_arg: str | None = None) -> str:
    if device_arg:
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


DEVICE = pick_device()
DTYPE = torch.float16 if DEVICE in ("cuda", "mps") else torch.float32
MODEL_CACHE: dict[str, OmniVoice] = {}


def load_voice_clone_prompt(prompt_path: str | Path) -> VoiceClonePrompt:
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


def load_speakers(speakers_path: str | Path | None = None) -> dict:
    path = Path(speakers_path) if speakers_path else SPEAKERS_PATH
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_speakers(speakers: dict, speakers_path: str | Path | None = None) -> None:
    path = Path(speakers_path) if speakers_path else SPEAKERS_PATH
    path.write_text(json.dumps(speakers, ensure_ascii=True, indent=2), encoding="utf-8")


def load_model(model_arg: str | None, device_arg: str | None = None) -> OmniVoice:
    model_name = (model_arg or DEFAULT_MODEL_ID).strip()
    device = pick_device(device_arg)
    dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
    model_source = resolve_model_source(model_name)
    return OmniVoice.from_pretrained(model_source, device_map=device, dtype=dtype)


def get_model(model_arg: str | None) -> OmniVoice:
    model_name = (model_arg or DEFAULT_MODEL_ID).strip()
    if model_name in MODEL_CACHE:
        return MODEL_CACHE[model_name]
    model = load_model(model_name)
    MODEL_CACHE[model_name] = model
    return model


def to_wav16(audio, model: OmniVoice):
    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return model.sampling_rate, wav16


def run_generate(model_arg: str | None = None, **kwargs):
    try:
        model = get_model(model_arg)
        audio = model.generate(**kwargs)[0]
        return to_wav16(audio, model), "Done."
    except Exception as e:
        return None, f"Error: {type(e).__name__}: {e}"


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
        return "\uff0c".join(zh), None
    return None, "Invalid instruct items selected."


def build_instruct(items, required: bool = False) -> str | None:
    instruct, error = build_instruct_from_items(items)
    if error:
        raise ValueError(error)
    if required and not instruct:
        raise ValueError("Please provide at least one --instruct-item.")
    return instruct


def generate_clone_with_speaker_id(
    text,
    speaker_id,
    model_id,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    preprocess_prompt,
    postprocess_output,
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

    kwargs = dict(
        text=text.strip(),
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
    return run_generate(model_arg=model_id, **kwargs)


def generate_clone_with_ref_audio(
    text,
    ref_audio,
    ref_text,
    model_id,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    preprocess_prompt,
    postprocess_output,
):
    if not text or not text.strip():
        return None, "Please input target text."
    if not ref_audio:
        return None, "Please upload reference audio."

    chosen_language = language.strip() if language else None
    instruct, instruct_error = build_instruct_from_items(instruct_items)
    if instruct_error:
        return None, instruct_error

    kwargs = dict(
        text=text.strip(),
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
    return run_generate(model_arg=model_id, **kwargs)


def generate_voice_design(
    text,
    model_id,
    language,
    instruct_items,
    num_step,
    guidance_scale,
    speed,
    duration,
    denoise,
    postprocess_output,
):
    if not text or not text.strip():
        return None, "Please input target text."

    chosen_language = language.strip() if language else None
    instruct, instruct_error = build_instruct_from_items(instruct_items)
    if instruct_error:
        return None, instruct_error
    if not instruct:
        return None, "Please choose at least one instruct item."

    kwargs = dict(
        text=text.strip(),
        language=chosen_language,
        instruct=instruct,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
        speed=float(speed) if speed is not None else 1.0,
        duration=float(duration) if duration else None,
        denoise=bool(denoise),
        postprocess_output=bool(postprocess_output),
    )
    return run_generate(model_arg=model_id, **kwargs)


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
    model = get_model(DEFAULT_MODEL_ID)

    try:
        prompt = model.create_voice_clone_prompt(
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
