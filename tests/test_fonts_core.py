import hashlib
import tempfile
import unittest
from pathlib import Path

from ppt_restore.rendering.fonts import FontInfo, FontRegistry


class FontRegistryTests(unittest.TestCase):
    def test_hash_and_character_coverage(self):
        payload = b"font fixture"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FixtureSans.ttf"
            path.write_bytes(payload)
            registry = FontRegistry(auto_scan=False)
            info = FontInfo(
                "Fixture Sans",
                str(path),
                hashlib.sha256(payload).hexdigest(),
                coverage=(65, 66),
            )
            registry.register(info)
            self.assertEqual(registry.find("Fixture Sans").sha256, info.sha256)
            self.assertTrue(info.supports("AB"))
            self.assertFalse(info.supports("AC"))

    def test_empty_directory_scan_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = FontRegistry([tmp])
            self.assertEqual(registry.entries, ())
            self.assertIsNone(registry.find("missing"))
            self.assertEqual(registry.report()["count"], 0)

    def test_find_rejects_family_without_required_glyphs(self):
        registry = FontRegistry(auto_scan=False)
        registry.register(
            FontInfo("Latin Only", "/tmp/latin-only.ttf", "x", coverage=(65, 66))
        )
        self.assertIsNotNone(registry.find("Latin Only", text="AB"))
        self.assertIsNone(registry.find("Latin Only", text="中文"))

    def test_collection_faces_with_same_path_are_distinct(self):
        registry = FontRegistry(auto_scan=False)
        registry.register(
            FontInfo("Fixture Regular", "/tmp/fixture.ttc", "x", font_number=0)
        )
        registry.register(
            FontInfo("Fixture Bold", "/tmp/fixture.ttc", "x", font_number=1, weight=700)
        )
        self.assertEqual(len(registry.entries), 2)
        self.assertEqual(registry.find("Fixture Bold").font_number, 1)


if __name__ == "__main__":
    unittest.main()
