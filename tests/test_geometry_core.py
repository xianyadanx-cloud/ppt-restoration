import unittest

from ppt_restore.rendering.geometry import (
    CanvasSpec,
    box_px_to_emu,
    norm_to_px,
    pt_to_emu,
    px_to_emu,
    px_to_pt,
)


class GeometryCoreTests(unittest.TestCase):
    def test_reference_canvas_and_round_trip_units(self):
        canvas = CanvasSpec()
        self.assertEqual(px_to_emu(1440, "x", canvas), canvas.width_emu)
        self.assertEqual(px_to_emu(810, "y", canvas), canvas.height_emu)
        self.assertEqual(norm_to_px(500, "x", canvas), 720)
        self.assertEqual(norm_to_px(500, "y", canvas), 405)
        self.assertAlmostEqual(px_to_pt(96), 72)
        self.assertEqual(pt_to_emu(12), 152400)

    def test_square_pixel_box_maps_to_equal_physical_dimensions(self):
        left, top, width, height = box_px_to_emu([100, 100, 120, 120], CanvasSpec())
        self.assertEqual(width, height)
        self.assertGreater(left, 0)
        self.assertGreater(top, 0)


if __name__ == "__main__":
    unittest.main()
