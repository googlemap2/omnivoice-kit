import unittest

from backend.settings import AppSettings, SettingsStore, merge_translation_provider_config
from pathlib import Path
import tempfile


class TranslationSettingsTests(unittest.TestCase):
    def test_merge_translation_provider_config(self) -> None:
        merged = merge_translation_provider_config(
            {},
            deepl_api_key="secret-deepl",
            microsoft_api_key="secret-ms",
            microsoft_region="eastus",
            nllb_model_id="facebook/nllb-200-distilled-600M",
        )
        self.assertEqual(merged["deepl"]["api_key"], "secret-deepl")
        self.assertEqual(merged["microsoft"]["api_key"], "secret-ms")
        self.assertEqual(merged["microsoft"]["region"], "eastus")
        self.assertEqual(merged["nllb"]["model_id"], "facebook/nllb-200-distilled-600M")

    def test_save_and_load_provider_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            store = SettingsStore(path)
            settings = AppSettings(
                translation_provider_config=merge_translation_provider_config(
                    None,
                    deepl_api_key="abc123",
                )
            )
            store.save(settings)
            loaded = store.load()
            self.assertEqual(loaded.translation_provider_config["deepl"]["api_key"], "abc123")


if __name__ == "__main__":
    unittest.main()
