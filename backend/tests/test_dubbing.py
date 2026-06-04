import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import soundfile as sf

from backend.dubbing import (
    dub_file,
    fit_audio_to_duration,
    next_output_folder,
    normalize_speaker_voice_map,
    place_segment,
    sanitize_folder_name,
    validate_speaker_voice_map,
    voice_for_segment,
)
from backend.subtitles import SubtitleSegment
from backend.translation import TranslationResult, TranslationSegment


class DubbingAudioTests(unittest.TestCase):
    def test_fit_audio_truncates(self) -> None:
        audio = np.arange(10, dtype=np.float32)
        fitted = fit_audio_to_duration(audio, sample_rate=10, duration=0.5)
        self.assertEqual(fitted.tolist(), [0, 1, 2, 3, 4])

    def test_fit_audio_pads(self) -> None:
        audio = np.ones(3, dtype=np.float32)
        fitted = fit_audio_to_duration(audio, sample_rate=10, duration=0.5)
        self.assertEqual(fitted.size, 5)
        self.assertEqual(fitted[:3].tolist(), [1, 1, 1])
        self.assertEqual(fitted[3:].tolist(), [0, 0])

    def test_place_segment_adds_to_timeline(self) -> None:
        timeline = np.zeros(10, dtype=np.float32)
        place_segment(timeline, np.ones(3, dtype=np.float32), sample_rate=10, start=0.2, end=0.5)
        self.assertEqual(timeline.tolist(), [0, 0, 1, 1, 1, 0, 0, 0, 0, 0])

    def test_sanitize_folder_name(self) -> None:
        self.assertEqual(sanitize_folder_name("My Video!.mp4"), "My-Video-.mp4")
        self.assertEqual(sanitize_folder_name("   "), "dubbing")

    def test_next_output_folder_uses_incrementing_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first_name, first_path = next_output_folder(tmp, Path("My Video.mp4"))
            second_name, second_path = next_output_folder(tmp, Path("My Video.mp4"))
            custom_name, custom_path = next_output_folder(tmp, Path("ignored.mp4"), folder_name="Custom Name")
            self.assertEqual(first_name, "My-Video")
            self.assertEqual(second_name, "My-Video-2")
            self.assertEqual(custom_name, "Custom-Name")
            self.assertTrue(first_path.exists())
            self.assertTrue(second_path.exists())
            self.assertTrue(custom_path.exists())

    def test_voice_for_segment_uses_speaker_mapping(self) -> None:
        mapping = {"SPEAKER_00": "alice", "SPEAKER_01": "bob"}
        self.assertEqual(voice_for_segment("default", "SPEAKER_00", mapping), "alice")
        self.assertEqual(voice_for_segment("default", "SPEAKER_02", mapping), "default")
        self.assertEqual(voice_for_segment("default", None, mapping), "default")

    def test_normalize_speaker_voice_map_strips_empty_values(self) -> None:
        self.assertEqual(
            normalize_speaker_voice_map({" SPEAKER_00 ": " alice ", "": "skip", "SPEAKER_01": ""}),
            {"SPEAKER_00": "alice"},
        )

    def test_validate_speaker_voice_map_rejects_missing_voice(self) -> None:
        with self.assertRaises(ValueError):
            validate_speaker_voice_map("missing-default", {"SPEAKER_00": "missing-speaker"})

    def test_dub_file_smoke_with_short_audio_fixture_and_mocked_backends(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_audio = tmp_path / "input.wav"
            sf.write(input_audio, np.zeros(2400, dtype=np.float32), 24000)

            subtitle_segments = [
                SubtitleSegment(
                    id=0,
                    start=0.0,
                    end=0.5,
                    text="Hello",
                    speaker="SPEAKER_00",
                    metadata={"speaker": "SPEAKER_00"},
                )
            ]
            translated = TranslationResult(
                text="Xin chao",
                source_language="en",
                target_language="vi",
                provider="passthrough",
                segments=[
                    TranslationSegment(
                        id=0,
                        text="Hello",
                        start=0.0,
                        end=0.5,
                        translated_text="Xin chao",
                        metadata={"speaker": "SPEAKER_00"},
                    )
                ],
            )

            def fake_extract_audio(_source: Path, destination: Path) -> Path:
                sf.write(destination, np.zeros(2400, dtype=np.float32), 24000)
                return destination

            profiles = [SimpleNamespace(id="default"), SimpleNamespace(id="alice")]
            with (
                patch("backend.dubbing.get_profile_store") as get_profile_store,
                patch("backend.dubbing.extract_audio", side_effect=fake_extract_audio),
                patch("backend.dubbing.transcribe_file", return_value=SimpleNamespace(language="en")),
                patch("backend.dubbing.from_transcription_result", return_value=subtitle_segments),
                patch("backend.dubbing.translate_segments", return_value=translated),
                patch(
                    "backend.dubbing.generate_clone_with_speaker_id",
                    return_value=((24000, np.ones(12000, dtype=np.int16)), "ok"),
                ) as generate_tts,
                patch("backend.dubbing.has_video_stream", return_value=False),
            ):
                get_profile_store.return_value.list_profiles.return_value = profiles
                result = dub_file(
                    input_path=input_audio,
                    voice="default",
                    target_language="vi",
                    output_dir=tmp_path / "out",
                    speaker_voice_map={"SPEAKER_00": "alice"},
                )

            self.assertEqual(result.segment_count, 1)
            self.assertEqual(result.speaker_voices, {"SPEAKER_00": "alice"})
            self.assertEqual(result.segment_voices[0]["voice"], "alice")
            self.assertTrue(Path(result.dubbed_audio_path).exists())
            self.assertTrue(Path(result.srt_path).exists())
            self.assertTrue(Path(result.vtt_path).exists())
            manifest = json.loads(Path(result.voice_manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest[0]["speaker"], "SPEAKER_00")
            self.assertEqual(manifest[0]["voice"], "alice")
            generate_tts.assert_called_once()
            self.assertEqual(generate_tts.call_args.kwargs["speaker_id"], "alice")


if __name__ == "__main__":
    unittest.main()
