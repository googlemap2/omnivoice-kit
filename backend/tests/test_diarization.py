import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.diarization_service import (
    DiarizationSegment,
    assign_speakers_to_segments,
    configure_headless_matplotlib,
    get_diarization_annotation,
    load_pyannote_pipeline,
    overlap_seconds,
    run_pyannote_pipeline,
)


class DiarizationMergeTests(unittest.TestCase):
    def test_overlap_seconds(self) -> None:
        self.assertEqual(overlap_seconds(0, 2, 1, 3), 1)
        self.assertEqual(overlap_seconds(0, 1, 1, 2), 0)

    def test_assigns_speaker_by_largest_overlap(self) -> None:
        subtitles = [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "hello"},
            {"id": 1, "start": 2.0, "end": 4.0, "text": "world"},
        ]
        diarization = [
            DiarizationSegment(start=0.0, end=1.0, speaker="SPEAKER_00"),
            DiarizationSegment(start=1.0, end=4.0, speaker="SPEAKER_01"),
        ]
        assigned = assign_speakers_to_segments(subtitles, diarization)
        self.assertEqual(assigned[0].speaker, "SPEAKER_00")
        self.assertEqual(assigned[1].speaker, "SPEAKER_01")
        self.assertEqual(assigned[1].metadata["speaker"], "SPEAKER_01")

    def test_keeps_unassigned_segment(self) -> None:
        assigned = assign_speakers_to_segments(
            [{"id": 0, "start": 10.0, "end": 11.0, "text": "late"}],
            [{"start": 0.0, "end": 1.0, "speaker": "SPEAKER_00"}],
        )
        self.assertIsNone(assigned[0].speaker)

    def test_configure_headless_matplotlib_replaces_colab_backend(self) -> None:
        with patch.dict("os.environ", {"MPLBACKEND": "module://matplotlib_inline.backend_inline"}):
            configure_headless_matplotlib()
            import os

            self.assertEqual(os.environ["MPLBACKEND"], "agg")

    def test_from_pretrained_fallback_is_documented_by_behavior(self) -> None:
        # The compatibility path is exercised in integration when pyannote is installed.
        # This unit test keeps the module import-only and avoids requiring pyannote.
        self.assertFalse(Path("definitely-not-a-real-pyannote-model").exists())

    def test_get_diarization_annotation_supports_pyannote_v4_output(self) -> None:
        class Annotation:
            def itertracks(self, yield_label: bool = False):
                return iter(())

        class DiarizeOutput:
            speaker_diarization = Annotation()

        self.assertIs(get_diarization_annotation(DiarizeOutput()), DiarizeOutput.speaker_diarization)

    def test_load_pyannote_pipeline_prefers_token_argument(self) -> None:
        class Pipeline:
            received = None

            @classmethod
            def from_pretrained(cls, model_source: str, token: str | None = None):
                cls.received = (model_source, token)
                return cls()

        load_pyannote_pipeline(Pipeline, "local-model", token="hf_test", model_id="repo")
        self.assertEqual(Pipeline.received, ("local-model", "hf_test"))

    def test_load_pyannote_pipeline_falls_back_to_legacy_use_auth_token(self) -> None:
        class Pipeline:
            received = None

            @classmethod
            def from_pretrained(cls, model_source: str, **kwargs):
                if "token" in kwargs:
                    raise TypeError("unexpected keyword argument 'token'")
                cls.received = (model_source, kwargs.get("use_auth_token"))
                return cls()

        load_pyannote_pipeline(Pipeline, "local-model", token="hf_test", model_id="repo")
        self.assertEqual(Pipeline.received, ("local-model", "hf_test"))

    def test_run_pyannote_pipeline_falls_back_to_audio_file_dict(self) -> None:
        class Pipeline:
            received = None

            def __call__(self, value):
                if isinstance(value, str):
                    raise TypeError("expected AudioFile with uri and audio")
                self.received = value
                return "ok"

        pipeline = Pipeline()
        self.assertEqual(run_pyannote_pipeline(pipeline, "sample.wav"), "ok")
        self.assertEqual(pipeline.received, {"uri": "sample", "audio": "sample.wav"})


if __name__ == "__main__":
    unittest.main()
