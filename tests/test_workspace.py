"""Integration and Unit Tests for PPT Restoration Workspace."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder, parse_color, normalize_box
from tools.slice import slice_image
from tools.merge import merge_pptx_files


class TestPPTRestorationWorkspace(unittest.TestCase):

    def test_color_parsing(self):
        self.assertIsNotNone(parse_color("#2563EB"))
        self.assertIsNotNone(parse_color("2563EB"))
        self.assertIsNotNone(parse_color((37, 99, 235)))
        self.assertIsNotNone(parse_color("blue"))
        self.assertIsNone(parse_color("transparent"))

    def test_coordinate_normalization(self):
        l, t, w, h = normalize_box([50, 100, 400, 300])
        self.assertEqual((l, t, w, h), (50.0, 100.0, 400.0, 300.0))

        # Clamp test
        l, t, w, h = normalize_box([950, 950, 200, 200])
        self.assertEqual(l, 950.0)
        self.assertEqual(t, 950.0)
        self.assertEqual(w, 50.0)  # Clamped to not exceed 1000
        self.assertEqual(h, 50.0)

    def test_slide_builder_full_elements(self):
        builder = SlideBuilder(aspect_ratio="16:9", bg_color="#F8FAFC")
        builder.add_header(title="Test Slide Title", subtitle="Test Subtitle", category_tag="TEST")
        builder.add_card(box=[40, 200, 280, 500], bg_color="#FFFFFF", border_color="#E2E8F0", radius=True)
        builder.add_badge(box=[60, 220, 100, 40], text="STATUS")
        builder.add_textbox(box=[60, 280, 240, 200], text="Sample text content")
        builder.add_bullet_list(box=[60, 500, 240, 180], items=["Item 1", "Item 2"])
        builder.add_chart(
            box=[350, 200, 280, 500],
            chart_type="column",
            categories=["A", "B", "C"],
            series=[{"name": "Metric", "values": [10, 20, 30]}],
        )
        builder.add_table(
            box=[660, 200, 280, 500],
            headers=["Col 1", "Col 2"],
            rows=[["Row 1", "Val 1"], ["Row 2", "Val 2"]],
        )
        out_file = "output/test_slide.pptx"
        builder.save(out_file)
        self.assertTrue(os.path.exists(out_file))

    def test_image_slicing(self):
        if os.path.exists("examples/sample_slide.png"):
            out_crop = "assets/test_crop.png"
            slice_image("examples/sample_slide.png", box=[100, 100, 200, 200], output_path=out_crop)
            self.assertTrue(os.path.exists(out_crop))

    def test_gradient_card(self):
        builder = SlideBuilder(aspect_ratio="16:9")
        card = builder.add_card(
            box=[100, 100, 400, 300],
            gradient_colors=["#2563EB", "#7C3AED"],
            gradient_angle=45.0,
            radius=True,
        )
        self.assertIsNotNone(card)

    def test_progress_bar_and_kpi_card(self):
        builder = SlideBuilder(aspect_ratio="16:9")
        builder.add_progress_bar(box=[100, 100, 200, 15], pct=0.84, bar_color="#EA580C")
        builder.add_kpi_card(box=[350, 100, 120, 90], top_tag="规模缺口", value="38万", bottom_badge="缺口16%")
        out_test = "output/test_components.pptx"
        builder.save(out_test)
        self.assertTrue(os.path.exists(out_test))

    def test_sdd_lifecycle_engine(self):
        import subprocess
        # Test sdd status
        res_status = subprocess.run([sys.executable, "tools/sdd.py", "status"], capture_output=True, text=True)
        self.assertEqual(res_status.returncode, 0)
        # Test sdd sync
        res_sync = subprocess.run([sys.executable, "tools/sdd.py", "sync", "--desc", "单元测试同步校验", "--impact", "spec,plan,tasks,eval"], capture_output=True, text=True)
        self.assertEqual(res_sync.returncode, 0)


    def test_cumulative_building(self):
        from slides.build_slide_02 import build_slide_02
        out_cum = "output/test_cum_build.pptx"
        build_slide_02(cumulative_up_to=2, output_path=out_cum)
        self.assertTrue(os.path.exists(out_cum))


if __name__ == "__main__":
    unittest.main()
