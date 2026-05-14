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


def to_wav16(audio):
    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return MODEL.sampling_rate, wav16


def generate_clone_with_speaker_id(text, speaker_id, language, num_step, guidance_scale):
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

    audio = MODEL.generate(
        text=text.strip(),
        language=chosen_language,
        voice_clone_prompt=voice_clone_prompt,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
    )[0]

    return to_wav16(audio), "Done."


def generate_clone_with_ref_audio(text, ref_audio, ref_text, language, num_step, guidance_scale):
    if not text or not text.strip():
        return None, "Please input target text."
    if not ref_audio:
        return None, "Please upload reference audio."

    chosen_language = language.strip() if language else None
    audio = MODEL.generate(
        text=text.strip(),
        ref_audio=ref_audio,
        ref_text=ref_text.strip() if ref_text else None,
        language=chosen_language,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
    )[0]

    return to_wav16(audio), "Done."


def get_speaker_choices():
    speakers = load_speakers()
    return [""] + sorted(speakers.keys())


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
                    sid_num_step = gr.Slider(8, 64, value=16, step=1, label="Inference Steps")
                    sid_guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
                    sid_run = gr.Button("Generate", variant="primary")
                with gr.Column():
                    sid_out_audio = gr.Audio(type="numpy", label="Output")
                    sid_status = gr.Textbox(label="Status")

            sid_run.click(
                fn=generate_clone_with_speaker_id,
                inputs=[sid_text, sid_speaker_id, sid_language, sid_num_step, sid_guidance_scale],
                outputs=[sid_out_audio, sid_status],
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
                    ref_num_step = gr.Slider(8, 64, value=16, step=1, label="Inference Steps")
                    ref_guidance_scale = gr.Slider(0.0, 4.0, value=2.0, step=0.1, label="Guidance Scale")
                    ref_run = gr.Button("Generate", variant="primary")
                with gr.Column():
                    ref_out_audio = gr.Audio(type="numpy", label="Output")
                    ref_status = gr.Textbox(label="Status")

            ref_run.click(
                fn=generate_clone_with_ref_audio,
                inputs=[ref_text_target, ref_audio, ref_text, ref_language, ref_num_step, ref_guidance_scale],
                outputs=[ref_out_audio, ref_status],
            )


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7861)
