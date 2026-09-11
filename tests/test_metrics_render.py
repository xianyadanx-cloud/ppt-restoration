import unittest

from PIL import Image, ImageDraw

from ppt_restore.quality.metrics import (
    MetricEngine,
    bbox_center_error,
    bbox_iou,
    calculate_mse_and_ssim,
)


class MetricTests(unittest.TestCase):
    def test_identical_images_are_exact(self):
        image = Image.new("RGB", (64, 64), "white")
        mse, ssim = calculate_mse_and_ssim(image, image)
        self.assertEqual(mse, 0.0)
        self.assertEqual(ssim, 1.0)

    def test_local_error_is_reported(self):
        truth = Image.new("RGB", (64, 64), "white")
        rendered = truth.copy()
        ImageDraw.Draw(rendered).rectangle((0, 0, 15, 15), fill="black")
        report = MetricEngine().evaluate(None, truth, rendered)
        self.assertGreater(report.metrics["mse"], 0)
        self.assertGreater(report.metrics["explicit_error_rate"], 0)
        self.assertFalse(report.passed)

    def test_geometry_metrics(self):
        self.assertEqual(bbox_iou((0, 0, 10, 10), (0, 0, 10, 10)), 1.0)
        self.assertEqual(bbox_center_error((0, 0, 10, 10), (2, 0, 10, 10)), 2.0)


if __name__ == "__main__":
    unittest.main()
