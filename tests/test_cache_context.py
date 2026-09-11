import tempfile
import unittest
from pathlib import Path

from ppt_restore.quality.cache_context import visual_cache_context


class CacheContextTests(unittest.TestCase):
    def test_reference_fonts_renderer_and_evaluation_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "source.png"
            image.write_bytes(b"reference")
            font = root / "face.ttc"
            font.write_bytes(b"font version one")

            def context(renderer="v1", region="b1"):
                return visual_cache_context(image, renderer, {"region": region}, [root])

            original = context()
            self.assertEqual(original, context())
            font.write_bytes(b"font version two")
            self.assertNotEqual(
                original["font_files_sha256"], context()["font_files_sha256"]
            )
            image.write_bytes(b"changed source")
            self.assertNotEqual(
                original["reference_sha256"], context()["reference_sha256"]
            )
            self.assertNotEqual(context(), context(renderer="v2"))
            self.assertNotEqual(context(), context(region="b2"))
