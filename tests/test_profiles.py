import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voicekit.profiles import VoiceProfileStore


class VoiceProfileStoreTests(unittest.TestCase):
    def test_legacy_profile_records_gain_gallery_metadata_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "speakers.json"
            store_path.write_text(
                json.dumps(
                    {
                        "alice": {
                            "name": "Alice",
                            "type": "clone",
                            "prompt_path": "assets/speakers/alice.pt",
                            "language": "vi",
                        }
                    }
                ),
                encoding="utf-8",
            )
            profile = VoiceProfileStore(store_path).get_profile("alice")

            self.assertIsNotNone(profile)
            self.assertEqual(profile.tags, [])
            self.assertFalse(profile.favorite)
            self.assertIsNone(profile.notes)
            self.assertIsNone(profile.preview_path)
            self.assertEqual(profile.asset_dir, "assets/voices/alice")

    def test_update_and_search_gallery_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = VoiceProfileStore(Path(tmp) / "speakers.json")
            store.create_profile("alice", "assets/speakers/alice.pt", language="vi", ref_text="Xin chao")
            store.create_profile("bob", "assets/speakers/bob.pt", language="en", ref_text="Hello")

            updated = store.update_profile_metadata(
                "alice",
                tags=[" warm ", "narrator", "warm"],
                favorite=True,
                notes="Vietnamese narrator",
            )

            self.assertEqual(updated.tags, ["warm", "narrator"])
            self.assertTrue(updated.favorite)
            self.assertEqual(store.search_profiles(query="narrator"), [updated])
            self.assertEqual(store.search_profiles(language="vi"), [updated])
            self.assertEqual(store.search_profiles(favorite=True), [updated])
            self.assertEqual(store.search_profiles(tags=["warm"]), [updated])

    def test_voice_package_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "assets" / "voices"
            with patch("voicekit.profiles.DEFAULT_VOICE_ASSET_ROOT", asset_root):
                source_store = VoiceProfileStore(root / "source.json")
                prompt_path = asset_root / "alice" / "prompt.pt"
                prompt_path.parent.mkdir(parents=True)
                prompt_path.write_bytes(b"prompt")
                preview_path = asset_root / "alice" / "preview.wav"
                preview_path.write_bytes(b"preview")
                profile = source_store.create_profile(
                    "alice",
                    str(prompt_path),
                    language="vi",
                    ref_text="Xin chao",
                    name="Alice",
                )
                profile = source_store.update_profile_metadata(
                    profile.id,
                    tags=["warm"],
                    favorite=True,
                    notes="Narrator",
                    preview_path=str(preview_path),
                )

                package_path = source_store.export_package("alice", root / "alice.voicepkg.zip")

                target_store = VoiceProfileStore(root / "target.json")
                imported = target_store.import_package(package_path, profile_id="alice-import")

            self.assertEqual(imported.id, "alice-import")
            self.assertEqual(imported.name, "Alice")
            self.assertEqual(imported.language, "vi")
            self.assertEqual(imported.tags, ["warm"])
            self.assertTrue(imported.favorite)
            self.assertTrue(Path(imported.prompt_path).is_file())
            self.assertTrue(Path(imported.preview_path or "").is_file())
            self.assertEqual(Path(imported.prompt_path).read_bytes(), b"prompt")

    def test_voice_package_import_rejects_existing_profile_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "assets" / "voices"
            with patch("voicekit.profiles.DEFAULT_VOICE_ASSET_ROOT", asset_root):
                source_store = VoiceProfileStore(root / "source.json")
                prompt_path = asset_root / "alice" / "prompt.pt"
                prompt_path.parent.mkdir(parents=True)
                prompt_path.write_bytes(b"prompt")
                source_store.create_profile("alice", str(prompt_path))
                package_path = source_store.export_package("alice", root / "alice.voicepkg.zip")

                target_store = VoiceProfileStore(root / "target.json")
                target_store.import_package(package_path)
                with self.assertRaises(ValueError):
                    target_store.import_package(package_path)


if __name__ == "__main__":
    unittest.main()
