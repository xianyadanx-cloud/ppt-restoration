import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.platform.evidence import extract_evidence, read_evidence
from ppt_restore.platform.ocr import ImportedTextProvider, OcrProvider, TextDetection


class _FailingProvider(OcrProvider):
    def __init__(self, name, result=None, error=None):
        self.name = name
        self.result = list(result or [])
        self.error = error

    @property
    def available(self):
        return True

    def recognize(self, image, regions=None):
        if self.error:
            raise RuntimeError(self.error)
        return list(self.result)


class EvidenceTests(unittest.TestCase):
    def test_evidence_keeps_components_outside_scene_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "canonical.png"
            image = Image.new("RGB", (1440, 810), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                (60, 60, 680, 220), fill="#DCEBFF", outline="#2457A6", width=4
            )
            draw.line((40, 300, 1400, 300), fill="#334155", width=3)
            image.save(image_path)
            provider = ImportedTextProvider(
                [TextDetection("标题", (60, 60, 120, 40), 0.99, "imported")]
            )
            out = root / "evidence.json"
            bundle = extract_evidence(
                image_path, ocr_provider=provider, output_path=out
            )
            self.assertEqual(bundle.canvas["width_px"], 1440)
            self.assertEqual(bundle.ocr_lines[0]["text"], "标题")
            self.assertTrue(bundle.visual_primitives)
            self.assertTrue(
                all("element_type" not in item for item in bundle.visual_primitives)
            )
            self.assertEqual(read_evidence(out), bundle)

    def test_missing_ocr_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.png"
            Image.new("RGB", (1440, 810), "white").save(path)
            bundle = extract_evidence(path, ocr_mode="auto", ocr_provider=False)
            self.assertEqual(bundle.producer["ocr_status"], "unavailable")
            self.assertIn("OCR provider unavailable", bundle.producer["warning"])

    def test_provider_failure_and_fallback_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "slide.png"
            Image.new("RGB", (1440, 810), "white").save(path)
            out = root / "evidence.json"
            bundle = extract_evidence(
                path,
                ocr_provider=[
                    _FailingProvider("mac_vision", error="Swift SDK mismatch"),
                    _FailingProvider(
                        "tesseract",
                        [TextDetection("fallback", (10, 10, 80, 20), 0.9, "tesseract")],
                    ),
                ],
                output_path=out,
            )
            persisted = read_evidence(out)
            self.assertEqual(bundle.producer["ocr_status"], "completed")
            self.assertEqual(bundle.producer["ocr_provider"], "tesseract")
            self.assertEqual(
                [a["status"] for a in bundle.producer["ocr_attempts"]],
                ["failed", "completed"],
            )
            self.assertIn("Swift SDK mismatch", bundle.producer["warning"][0])
            self.assertEqual(
                persisted.producer["ocr_attempts"], bundle.producer["ocr_attempts"]
            )

    def test_all_provider_failures_keep_zero_ocr_degraded_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "slide.png"
            Image.new("RGB", (1440, 810), "white").save(path)
            bundle = extract_evidence(
                path,
                ocr_provider=[
                    _FailingProvider("mac_vision", error="vision failed"),
                    _FailingProvider("tesseract", error="tesseract failed"),
                ],
            )
            self.assertEqual(bundle.ocr_lines, ())
            self.assertEqual(bundle.producer["ocr_status"], "failed")
            self.assertTrue(bundle.producer["ocr_degraded"])
            self.assertTrue(bundle.producer["ocr_zero_detections"])
            self.assertTrue(bundle.producer["ocr_requires_manual_review"])
            self.assertEqual(len(bundle.producer["ocr_attempts"]), 2)

    def test_successful_zero_detection_is_persisted_as_zero_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.png"
            Image.new("RGB", (1440, 810), "white").save(path)
            bundle = extract_evidence(
                path, ocr_provider=[_FailingProvider("mac_vision")]
            )
            self.assertEqual(bundle.producer["ocr_status"], "zero_detections")
            self.assertTrue(bundle.producer["ocr_zero_detections"])
            self.assertTrue(
                any(
                    "zero detections" in warning
                    for warning in bundle.producer["warning"]
                )
            )


if __name__ == "__main__":
    unittest.main()
