import json
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
