import unittest

from PIL import Image, ImageDraw

from ppt_restore.quality.metrics import (
    MetricEngine,
    bbox_center_error,
    bbox_iou,
    calculate_best_shift_ssim,
    calculate_blur_l1,
    calculate_ink_iou,
    calculate_mse_and_ssim,
    calculate_tolerant_edge_f1,
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

    def test_shift_tolerant_metrics_keep_a_slope(self):
        truth = Image.new("RGB", (48, 32), "white")
        ImageDraw.Draw(truth).rectangle((8, 8, 20, 22), fill="black")
        shifted = Image.new("RGB", truth.size, "white")
        shifted.paste(truth, (3, 0))
        self.assertGreater(calculate_ink_iou(shifted, truth), 0.2)
        self.assertGreater(
            calculate_tolerant_edge_f1(shifted, truth), 0.2
        )
        near = calculate_blur_l1(shifted, truth)
        far = Image.new("RGB", truth.size, "white")
        far.paste(truth, (16, 0))
        self.assertLess(near, calculate_blur_l1(far, truth))
        report = calculate_best_shift_ssim(shifted, truth, max_shift=3)
        self.assertGreaterEqual(report["ssim_best_shift"], report["ssim"])


if __name__ == "__main__":
    unittest.main()
