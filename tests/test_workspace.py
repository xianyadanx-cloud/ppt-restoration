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


    def test_design_tokens_and_text_metrics(self):
        from tools.pptx_helper import Tokens, estimate_text_width_pt, calculate_safe_font_size
        # Test Design Tokens
        self.assertEqual(Tokens.FONT_TITLE_LG, 32.0)
        self.assertEqual(Tokens.FONT_BADGE, 8.5)
        self.assertEqual(Tokens.GAP_SM, 8.0)

        # Test Text Physical Metrics Estimation
        w_cjk = estimate_text_width_pt("季度攻坚", 10.0)
        self.assertAlmostEqual(w_cjk, 40.0, delta=1.0)
        w_ascii = estimate_text_width_pt("1234", 10.0)
        self.assertLess(w_ascii, 30.0)

        # Test Safe Font Size Auto-Fit Calculation
        safe_size = calculate_safe_font_size(
            text="非常长的一个业务主标题文本内容不能折行",
            target_width_pt=100.0,
            desired_font_size=24.0,
            min_font_size=8.0,
        )
        self.assertLess(safe_size, 24.0)
        self.assertGreaterEqual(safe_size, 8.0)

    def test_flex_stack_and_grid_layout(self):
        from tools.pptx_helper import SlideBuilder, Tokens
        builder = SlideBuilder(aspect_ratio="16:9")

        # 1. Test Grid Layout
        grid_cells = builder.add_grid(box=[50, 200, 900, 300], cols=3, rows=1, gap_x=20.0)
        self.assertEqual(len(grid_cells), 3)
        self.assertAlmostEqual(grid_cells[0][2], (900 - 40) / 3.0, delta=0.1)

        # 2. Test Stack Layout
        stack_shapes = builder.add_stack(
            box=list(grid_cells[0]),
            direction="vertical",
            gap=Tokens.GAP_SM,
            align="center",
            children=[
                {"type": "badge", "text": "核心标签", "bg_color": "#2563EB", "text_color": "#FFFFFF"},
                {"type": "text", "text": "38万", "font_size": Tokens.FONT_KPI_VAL, "bold": True},
                {"type": "text", "text": "较上季度增加12%", "font_size": Tokens.FONT_BODY_SM, "font_color": "#64748B"},
            ],
            bg_color="#F8FAFC",
            border_color="#E2E8F0",
        )
        self.assertGreaterEqual(len(stack_shapes), 3)

        # 3. Test Flex Card
        flex_shapes = builder.add_flex_card(
            box=list(grid_cells[1]),
            badge="突破行动",
            kpi_value="84%",
            kpi_label="目标达成率",
            title="战略纵深拓展",
            body_items=["完成新渠道铺设", "留存率提升 5.2%"],
            bg_color="#FFFFFF",
            border_color="#CBD5E1",
        )
        self.assertGreaterEqual(len(flex_shapes), 1)

        out_flex = "output/test_flex_layout.pptx"
        builder.save(out_flex)
        self.assertTrue(os.path.exists(out_flex))

    def test_multi_agent_evaluation_metrics(self):
        from tools.eval_metrics import inspect_dom_picture_count, calculate_mse_and_ssim
        from PIL import Image

        # Test DOM picture count on clean PPTX
        dom_res = inspect_dom_picture_count("output/test_flex_layout.pptx")
        self.assertEqual(dom_res.get("status"), "PASS")
        self.assertEqual(dom_res.get("picture_count"), 0)

        # Test SSIM calculation
        img1 = Image.new("RGB", (200, 200), color=(255, 255, 255))
        img2 = Image.new("RGB", (200, 200), color=(255, 255, 255))
        mse, ssim = calculate_mse_and_ssim(img1, img2)
        self.assertEqual(ssim, 1.0)
        self.assertEqual(mse, 0.0)

    def test_orchestrator_cli(self):
        import subprocess
        # Test orchestrator status
        res = subprocess.run([sys.executable, "tools/orchestrator.py", "status"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

    def test_layout_linter(self):
        from tools.layout_linter import audit_layout
        res = audit_layout("output/slide_02.pptx")
        self.assertTrue(res["passed"])
        self.assertEqual(len(res["errors"]), 0)

    def test_skill_pipeline(self):
        from skills.spacing_grid.grid_calculator import calculate_grid_cells, compute_two_column_baseline
        from skills.vector_builder.code_generator import generate_python_block_code

        # 1. Test Spacing & Grid Skill
        baseline = compute_two_column_baseline(top=305.0, bottom=925.0)
        self.assertEqual(baseline["top_baseline"], 305.0)
        self.assertEqual(baseline["bottom_baseline"], 925.0)

        cells = calculate_grid_cells(parent_box=[100, 100, 800, 200], cols=4, rows=1, gap_x=10.0)
        self.assertEqual(len(cells), 4)

        # 2. Test Vector Builder Skill
        manifest = {
            "block_id": 5,
            "name": "Test Action Block",
            "function_name": "add_test_action_section",
            "elements": [
                {"type": "SHAPE_CIRCLE", "box": [510, 400, 24, 24], "text": "1", "bg_color": "#1B5B9E", "text_color": "#FFFFFF", "font_size": 11, "bold": True},
                {"type": "TEXT_PLAIN", "box": [544, 398, 410, 28], "text": "流量重构-突破渠道瓶颈", "font_size": 13, "font_color": "#0F172A", "bold": True}
            ]
        }
        code = generate_python_block_code(manifest)
        self.assertIn("def add_test_action_section", code)
        self.assertIn("add_badge", code)
        self.assertIn("add_textbox", code)


if __name__ == "__main__":
    unittest.main()
