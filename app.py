import gradio as gr
import numpy as np
import torch
from omnivoice import OmniVoice


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


DEVICE = pick_device()
DTYPE = torch.float16 if DEVICE in ("cuda", "mps") else torch.float32
MODEL = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=DEVICE, dtype=DTYPE)


def generate_clone(text, ref_audio, ref_text, language, num_step, guidance_scale):
    if not text or not text.strip():
        return None, "Please input target text."
    if not ref_audio:
        return None, "Please upload reference audio."

    audio = MODEL.generate(
        text=text.strip(),
        ref_audio=ref_audio,
        ref_text=ref_text.strip() if ref_text else None,
        language=language.strip() if language else None,
        num_step=int(num_step),
        guidance_scale=float(guidance_scale),
    )[0]

    wav16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    return (MODEL.sampling_rate, wav16), "Done."


with gr.Blocks(title="OmniVoice Voice Clone Kit") as demo:
    gr.Markdown("# OmniVoice Voice Clone Kit")
    gr.Markdown("Upload a reference voice (3-10s recommended), enter text, and synthesize cloned speech.")

    with gr.Row():
        with gr.Column():
            text = gr.Textbox(label="Target Text", lines=4)
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
        inputs=[text, ref_audio, ref_text, language, num_step, guidance_scale],
        outputs=[out_audio, status],
    )


if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7861)
