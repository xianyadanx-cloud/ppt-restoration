import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.contracts.models import AnalysisState
from ppt_restore.pipeline.canonicalize import canonicalize


class CanonicalizeTests(unittest.TestCase):
    def test_clean_screenshot_is_stable(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "input.png"
            image = Image.new("RGB", (1600, 900), "white")
            ImageDraw.Draw(image).rectangle((100, 100, 500, 400), fill="#336699")
            image.save(source)
            first, second = Path(td) / "a", Path(td) / "b"
            r1, r2 = canonicalize(source, first), canonicalize(source, second)
            self.assertEqual(r1.canonical_sha256, r2.canonical_sha256)
            with Image.open(first / "canonical.png") as canonical:
                self.assertEqual(canonical.size, (1440, 810))

    def test_low_confidence_is_review(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "input.png"
            Image.new("RGB", (800, 400), "white").save(source)
            result = canonicalize(source, Path(td) / "case", target_size=(1440, 810))
            # An ambiguous non-16:9 blank image must not be silently accepted.
            self.assertEqual(result.state, AnalysisState.NEEDS_REVIEW)

    def test_long_image_exposes_two_16_9_candidates(self):
        from ppt_restore.pipeline.canonicalize import detect_page_candidates

        image = Image.new("RGB", (1440, 1620), "#d0d0d0")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1439, 809), fill="#ffffff")
        draw.rectangle((0, 810, 1439, 1619), fill="#ffffff")
        candidates = detect_page_candidates(image)
        self.assertGreaterEqual(len(candidates), 2)
        self.assertTrue(
            all(
                abs((box[2] / float(box[3])) / (16 / 9) - 1) < 0.02
                for box in candidates[:2]
            )
        )

    def test_inset_pages_on_gray_pasteboard_are_detected(self):
        from ppt_restore.pipeline.canonicalize import detect_page_candidates

        image = Image.new("RGB", (1440, 1920), (209, 213, 214))
        draw = ImageDraw.Draw(image)
        draw.rectangle((69, 347, 1369, 1080), fill="white")
        draw.rectangle((69, 1115, 1369, 1848), fill="white")
        candidates = detect_page_candidates(image)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0], (69, 347, 1301, 734))
        self.assertEqual(candidates[1], (69, 1115, 1301, 734))


if __name__ == "__main__":
    unittest.main()
