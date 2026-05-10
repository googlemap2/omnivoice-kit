import gradio as gr
import numpy as np
import json
from pathlib import Path
import torch
from omnivoice import OmniVoice
from omnivoice.models.omnivoice import VoiceClonePrompt


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


DEVICE = pick_device()
DTYPE = torch.float16 if DEVICE in ("cuda", "mps") else torch.float32
MODEL = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=DEVICE, dtype=DTYPE)
SPEAKERS_PATH = Path("speakers.json")


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


def generate_clone(text, speaker_id, ref_audio, ref_text, language, num_step, guidance_scale):
    if not text or not text.strip():
        return None, "Please input target text."

    speakers = load_speakers()
    voice_clone_prompt = None
    chosen_language = language.strip() if language else None

    if speaker_id and speaker_id in speakers:
        cfg = speakers[speaker_id]
        voice_clone_prompt = load_voice_clone_prompt(cfg["prompt_path"])
        if not chosen_language:
            chosen_language = cfg.get("language")

    if voice_clone_prompt is not None:
        audio = MODEL.generate(
            text=text.strip(),
            language=chosen_language,
            voice_clone_prompt=voice_clone_prompt,
            num_step=int(num_step),
            guidance_scale=float(guidance_scale),
        )[0]
    else:
        if not ref_audio:
            return None, "Please choose speaker_id or upload reference audio."
        audio = MODEL.generate(
            text=text.strip(),
            ref_audio=ref_audio,
            ref_text=ref_text.strip() if ref_text else None,
            language=chosen_language,
            num_step=int(num_step),
            guidance_scale=float(guidance_scale),
        )[0]

    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return (MODEL.sampling_rate, wav16), "Done."


def get_speaker_choices():
    speakers = load_speakers()
    return [""] + sorted(speakers.keys())


with gr.Blocks(title="OmniVoice Voice Clone Kit") as demo:
    gr.Markdown("# OmniVoice Voice Clone Kit")
    gr.Markdown("Upload a reference voice (3-10s recommended), enter text, and synthesize cloned speech.")

    with gr.Row():
        with gr.Column():
            text = gr.Textbox(label="Target Text", lines=4)
            speaker_id = gr.Dropdown(
                choices=get_speaker_choices(),
                value="",
                label="Speaker ID (optional, from speakers.json)",
                allow_custom_value=False,
            )
            ref_audio = gr.Audio(type="filepath", label="Reference Audio")
            ref_text = gr.Textbox(label="Reference Transcript (optional)", lines=2)
            language = gr.Textbox(label="Language (optional, e.g. vi, en, Vietnamese)", lines=1)
            num_step = gr.Slider(8, 64, value=16, step=1, label="Inference Steps")
            guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
            run = gr.Button("Generate", variant="primary")
        with gr.Column():
            out_audio = gr.Audio(type="numpy", label="Output")
            status = gr.Textbox(label="Status")

    run.click(
        fn=generate_clone,
        inputs=[text, speaker_id, ref_audio, ref_text, language, num_step, guidance_scale],
        outputs=[out_audio, status],
    )


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7861)
