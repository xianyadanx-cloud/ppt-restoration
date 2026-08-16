"""Test optimized Block 1 and compare diff"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.pptx_helper import SlideBuilder
from tools.render_and_diff import compare_and_generate_diff

def test_optimized_block1():
    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")
    
    # Optimized Block 1 based on exact GT measurements
    # 1. Main Title
    builder.add_textbox(
        box=[26, 26, 600, 68],
        text="季度工作攻坚策略",
        font_size=38,
        font_color="#000000",
        bold=True,
    )
    # 2. Divider Line
    builder.add_card(
        box=[26, 96, 948, 1.5],
        bg_color="#D1D5DB",
        border_color="transparent"
    )
    # 3. Right Author Tag
    builder.add_textbox(
        box=[720, 35, 254, 55],
        text="@鱼丸PPT",
        font_size=22,
        font_color="#000000",
        bold=True,
        align="right",
    )

    output_path = "output/test_block1_opt.pptx"
    builder.save(output_path)
    
    # Render and diff
    os.system(f".venv/bin/python tools/render_and_diff.py {output_path} input/slide_02.png --crop-box 20 15 960 95 --block-title 'Block 1: Optimized Header' -o output/diff_block1_optimized.png")

if __name__ == "__main__":
    test_optimized_block1()
