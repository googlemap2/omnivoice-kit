import gradio as gr

from voicekit.core import (
    OMNIVOICE_LANGUAGE_CHOICES,
    OMNIVOICE_MODEL_CHOICES,
    VALID_INSTRUCTS,
    create_speaker_id,
    delete_speaker_id,
    generate_clone_with_ref_audio,
    generate_clone_with_speaker_id,
    generate_voice_design,
    get_speaker_choices,
    rename_speaker_id,
)
from voicekit.audio import EFFECT_PRESETS
from voicekit.asr import ASR_MODEL_CHOICES, DEFAULT_ASR_MODEL_ID, TRANSCRIPTION_FORMATS, transcribe_for_ui
from voicekit.history import list_history
from voicekit.model_store import DEFAULT_MODEL_ID
from voicekit.model_store import install_model, list_model_statuses
from voicekit.settings import AppSettings, load_settings, save_settings


DEVICE_CHOICES = ["", "cpu", "cuda", "mps"]
COMPUTE_TYPE_CHOICES = ["", "int8", "float16", "float32"]


def get_model_status_rows():
    return [status.to_dict() for status in list_model_statuses()]


def install_default_model():
    try:
        status = install_model(DEFAULT_MODEL_ID)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}", get_model_status_rows()
    message = "Model is installed." if status.installed else "Model install finished but files are incomplete."
    return message, get_model_status_rows()


def get_history_rows(limit=50):
    try:
        return list_history(limit=int(limit or 50))
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {e}"}]


def get_settings_dict():
    return load_settings().to_dict()


def save_settings_from_ui(default_model, default_device, default_effect_preset, output_dir):
    settings = AppSettings(
        default_model=default_model,
        default_device=default_device or None,
        default_effect_preset=default_effect_preset,
        output_dir=output_dir,
    )
    saved = save_settings(settings)
    return "Settings saved.", saved.to_dict()


APP_SETTINGS = load_settings()


with gr.Blocks(title="OmniVoice Voice Clone Kit") as demo:
    gr.Markdown("# OmniVoice Voice Clone Kit")
    gr.Markdown("Choose one mode: clone from `speaker_id` or clone from uploaded reference audio.")

    with gr.Tabs():
        with gr.Tab("OmniVoice"):
            with gr.Tabs():
                with gr.Tab("TTS by Speaker ID"):
                    with gr.Row():
                        with gr.Column():
                            sid_text = gr.Textbox(label="Target Text", lines=4)
                            sid_model = gr.Dropdown(
                                choices=OMNIVOICE_MODEL_CHOICES,
                                value=APP_SETTINGS.default_model,
                                label="Model",
                                allow_custom_value=True,
                            )
                            sid_speaker_id = gr.Dropdown(
                                choices=get_speaker_choices(),
                                value="",
                                label="Speaker ID (from speakers.json)",
                                allow_custom_value=False,
                            )
                            sid_language = gr.Dropdown(
                                choices=OMNIVOICE_LANGUAGE_CHOICES,
                                value=None,
                                label="Language (optional)",
                                allow_custom_value=True,
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
                            sid_effect_preset = gr.Dropdown(
                                choices=EFFECT_PRESETS,
                                value=APP_SETTINGS.default_effect_preset,
                                label="Effect Preset",
                            )
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
                            sid_model,
                            sid_language,
                            sid_instruct_items,
                            sid_num_step,
                            sid_guidance_scale,
                            sid_speed,
                            sid_duration,
                            sid_denoise,
                            sid_preprocess_prompt,
                            sid_postprocess_output,
                            sid_effect_preset,
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
                            ref_model = gr.Dropdown(
                                choices=OMNIVOICE_MODEL_CHOICES,
                                value=APP_SETTINGS.default_model,
                                label="Model",
                                allow_custom_value=True,
                            )
                            ref_audio = gr.Audio(type="filepath", label="Reference Audio")
                            ref_text = gr.Textbox(label="Reference Transcript (optional)", lines=2)
                            ref_language = gr.Dropdown(
                                choices=OMNIVOICE_LANGUAGE_CHOICES,
                                value=None,
                                label="Language (optional)",
                                allow_custom_value=True,
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
                            ref_effect_preset = gr.Dropdown(
                                choices=EFFECT_PRESETS,
                                value=APP_SETTINGS.default_effect_preset,
                                label="Effect Preset",
                            )
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
                            ref_model,
                            ref_language,
                            ref_instruct_items,
                            ref_num_step,
                            ref_guidance_scale,
                            ref_speed,
                            ref_duration,
                            ref_denoise,
                            ref_preprocess_prompt,
                            ref_postprocess_output,
                            ref_effect_preset,
                        ],
                        outputs=[ref_out_audio, ref_status],
                    )

                with gr.Tab("Voice Design"):
                    with gr.Row():
                        with gr.Column():
                            vd_text = gr.Textbox(label="Target Text", lines=4)
                            vd_model = gr.Dropdown(
                                choices=OMNIVOICE_MODEL_CHOICES,
                                value=APP_SETTINGS.default_model,
                                label="Model",
                                allow_custom_value=True,
                            )
                            vd_language = gr.Dropdown(
                                choices=OMNIVOICE_LANGUAGE_CHOICES,
                                value=None,
                                label="Language (optional)",
                                allow_custom_value=True,
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
                            vd_effect_preset = gr.Dropdown(
                                choices=EFFECT_PRESETS,
                                value=APP_SETTINGS.default_effect_preset,
                                label="Effect Preset",
                            )
                            vd_run = gr.Button("Generate", variant="primary")
                        with gr.Column():
                            vd_out_audio = gr.Audio(type="numpy", label="Output")
                            vd_status = gr.Textbox(label="Status")

                    vd_run.click(
                        fn=generate_voice_design,
                        inputs=[
                            vd_text,
                            vd_model,
                            vd_language,
                            vd_instruct_items,
                            vd_num_step,
                            vd_guidance_scale,
                            vd_speed,
                            vd_duration,
                            vd_denoise,
                            vd_postprocess_output,
                            vd_effect_preset,
                        ],
                        outputs=[vd_out_audio, vd_status],
                    )

                with gr.Tab("Create Speaker ID"):
                    with gr.Tabs():
                        with gr.Tab("Create"):
                            with gr.Row():
                                with gr.Column():
                                    cs_speaker_id = gr.Textbox(label="Speaker ID", lines=1)
                                    cs_ref_audio = gr.Audio(type="filepath", label="Reference Audio")
                                    cs_ref_text = gr.Textbox(label="Reference Transcript (optional)", lines=2)
                                    cs_language = gr.Dropdown(
                                        choices=OMNIVOICE_LANGUAGE_CHOICES,
                                        value=None,
                                        label="Language (optional)",
                                        allow_custom_value=True,
                                    )
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

                with gr.Tab("Models"):
                    with gr.Row():
                        with gr.Column():
                            model_refresh = gr.Button("Refresh Model Status")
                            model_install = gr.Button("Install Default Model", variant="primary")
                        with gr.Column():
                            model_status = gr.JSON(value=get_model_status_rows(), label="Model Status")
                            model_message = gr.Textbox(label="Install Status", lines=3)

                    model_refresh.click(
                        fn=get_model_status_rows,
                        inputs=[],
                        outputs=[model_status],
                    )
                    model_install.click(
                        fn=install_default_model,
                        inputs=[],
                        outputs=[model_message, model_status],
                    )

                with gr.Tab("Transcription"):
                    with gr.Row():
                        with gr.Column():
                            asr_audio = gr.Audio(type="filepath", label="Audio")
                            asr_model = gr.Dropdown(
                                choices=ASR_MODEL_CHOICES,
                                value=DEFAULT_ASR_MODEL_ID,
                                label="ASR Model",
                                allow_custom_value=True,
                            )
                            asr_language = gr.Textbox(value="", label="Language")
                            asr_device = gr.Dropdown(
                                choices=DEVICE_CHOICES,
                                value=APP_SETTINGS.default_device or "",
                                label="Device",
                            )
                            asr_compute_type = gr.Dropdown(
                                choices=COMPUTE_TYPE_CHOICES,
                                value="",
                                label="Compute Type",
                            )
                            asr_word_timestamps = gr.Checkbox(value=False, label="Word Timestamps")
                            asr_beam_size = gr.Slider(1, 10, value=5, step=1, label="Beam Size")
                            asr_format = gr.Dropdown(
                                choices=TRANSCRIPTION_FORMATS,
                                value="verbose_json",
                                label="Response Format",
                            )
                            asr_run = gr.Button("Transcribe", variant="primary")
                        with gr.Column():
                            asr_text = gr.Textbox(label="Transcript", lines=12)
                            asr_status = gr.Textbox(label="Status", lines=2)
                            asr_json = gr.JSON(label="Verbose Result")

                    asr_run.click(
                        fn=transcribe_for_ui,
                        inputs=[
                            asr_audio,
                            asr_model,
                            asr_language,
                            asr_device,
                            asr_compute_type,
                            asr_word_timestamps,
                            asr_beam_size,
                            asr_format,
                        ],
                        outputs=[asr_text, asr_status, asr_json],
                    )

                with gr.Tab("History"):
                    with gr.Row():
                        with gr.Column():
                            history_limit = gr.Number(value=50, label="Limit", precision=0)
                            history_refresh = gr.Button("Refresh History")
                        with gr.Column():
                            history_rows = gr.JSON(value=get_history_rows(), label="Generation History")

                    history_refresh.click(
                        fn=get_history_rows,
                        inputs=[history_limit],
                        outputs=[history_rows],
                    )

                with gr.Tab("Settings"):
                    with gr.Row():
                        with gr.Column():
                            settings_model = gr.Dropdown(
                                choices=OMNIVOICE_MODEL_CHOICES,
                                value=APP_SETTINGS.default_model,
                                label="Default Model",
                                allow_custom_value=True,
                            )
                            settings_device = gr.Dropdown(
                                choices=DEVICE_CHOICES,
                                value=APP_SETTINGS.default_device or "",
                                label="Default Device",
                                allow_custom_value=False,
                            )
                            settings_effect = gr.Dropdown(
                                choices=EFFECT_PRESETS,
                                value=APP_SETTINGS.default_effect_preset,
                                label="Default Effect Preset",
                            )
                            settings_output_dir = gr.Textbox(
                                value=APP_SETTINGS.output_dir,
                                label="Output Directory",
                            )
                            settings_save = gr.Button("Save Settings", variant="primary")
                            settings_refresh = gr.Button("Refresh Settings")
                        with gr.Column():
                            settings_message = gr.Textbox(label="Status", lines=2)
                            settings_json = gr.JSON(value=get_settings_dict(), label="Current Settings")

                    settings_save.click(
                        fn=save_settings_from_ui,
                        inputs=[settings_model, settings_device, settings_effect, settings_output_dir],
                        outputs=[settings_message, settings_json],
                    )
                    settings_refresh.click(
                        fn=get_settings_dict,
                        inputs=[],
                        outputs=[settings_json],
                    )

def main() -> None:
    demo.queue().launch(server_name="0.0.0.0", server_port=7861)


if __name__ == "__main__":
    main()
