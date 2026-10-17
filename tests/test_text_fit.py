import unittest

from ppt_restore.rendering.geometry import CanvasSpec
from ppt_restore.rendering.text_fit import expand_ink_frame, fit_text_frame, px_to_pt_canvas


class TextFitTests(unittest.TestCase):
    def test_canvas_point_size_is_not_96dpi(self):
        self.assertAlmostEqual(px_to_pt_canvas(1.5), 1.0)
        self.assertAlmostEqual(px_to_pt_canvas(45), 30.0)

    def test_fit_lifts_frame_and_matches_ink_height(self):
        fitted = fit_text_frame("增长", (100, 80, 100, 40), canvas=CanvasSpec())
        self.assertAlmostEqual(fitted["font_size_pt"], 30.3, delta=2.0)
        self.assertLess(fitted["bbox_px"][1], 80)
        self.assertGreater(fitted["bbox_px"][3], 40)

    def test_expand_ink_frame_moves_top_up(self):
        frame = expand_ink_frame((10, 50, 80, 30), 24, CanvasSpec(), ascent_gap_em=0.2)
        self.assertLess(frame[1], 50)
        self.assertGreater(frame[3], 30)


if __name__ == "__main__":
    unittest.main()
