import unittest

from PIL import Image

from ppt_restore.platform.ocr import (
    ImportedTextProvider,
    OcrProvider,
    TesseractOcrProvider,
    TextDetection,
    run_ocr,
)


class _FakeProvider(OcrProvider):
    def __init__(self, name, result=None, error=None, available=True):
        self.name = name
        self.result = list(result or [])
        self.error = error
        self._available = available
        self.calls = 0

    @property
    def available(self):
        return self._available

    def recognize(self, image, regions=None):
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return list(self.result)


class OcrCoreTests(unittest.TestCase):
    def test_imported_text_is_explicitly_labelled(self):
        detection = TextDetection("示例", (1, 2, 30, 12), 0.8, "imported_text")
        result = ImportedTextProvider([detection]).recognize(None)
        self.assertEqual(result[0].provider, "imported_text")
        self.assertEqual(result[0].bbox_px, (1, 2, 30, 12))

    def test_missing_local_backend_is_not_faked(self):
        provider = TesseractOcrProvider(executable=None)
        if not provider.available:
            with self.assertRaises(RuntimeError):
                provider.recognize(None)

    def test_runtime_cascade_continues_after_vision_execution_failure(self):
        vision = _FakeProvider("mac_vision", error="Swift SDK mismatch")
        tesseract = _FakeProvider(
            "tesseract", [TextDetection("fallback", (1, 2, 20, 10), 0.9, "tesseract")]
        )
        detections, attempts, warnings, selected, status = run_ocr(
            Image.new("RGB", (40, 20), "white"), [vision, tesseract]
        )
        self.assertEqual([d.text for d in detections], ["fallback"])
        self.assertEqual(selected, "tesseract")
        self.assertEqual(status, "completed")
        self.assertEqual([a["status"] for a in attempts], ["failed", "completed"])
        self.assertIn("Swift SDK mismatch", warnings[0])
        self.assertEqual(vision.calls, 1)
        self.assertEqual(tesseract.calls, 1)

    def test_runtime_cascade_records_all_failures(self):
        first = _FakeProvider("mac_vision", error="vision unavailable at runtime")
        second = _FakeProvider("tesseract", error="binary failed")
        detections, attempts, warnings, selected, status = run_ocr(
            Image.new("RGB", (40, 20), "white"), [first, second]
        )
        self.assertEqual(detections, [])
        self.assertIsNone(selected)
        self.assertEqual(status, "failed")
        self.assertEqual(len(attempts), 2)
        self.assertTrue(all(a["status"] == "failed" and a["error"] for a in attempts))
        self.assertEqual(len(warnings), 2)

    def test_zero_detections_are_distinct_from_provider_failure(self):
        provider = _FakeProvider("mac_vision", result=[])
        detections, attempts, warnings, selected, status = run_ocr(
            Image.new("RGB", (40, 20), "white"), [provider]
        )
        self.assertEqual(detections, [])
        self.assertEqual(status, "zero_detections")
        self.assertEqual(attempts[0]["status"], "zero_detections")
        self.assertFalse(warnings)


if __name__ == "__main__":
    unittest.main()
