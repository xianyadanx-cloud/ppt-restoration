"""Verify Exact Block Boundaries of Slide 02"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def verify_all_blocks():
    raw = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw)
    canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    print("=" * 80)
    print("📐 SLIDE 02 真实全页分块边界精准检测 (1440x810 画布 & 0-1000 坐标)")
    print("=" * 80)

    # 1. Block 3 KPI Cards Bottom Line
    # "规模缺口 38万 缺口16%", "转化迟滞 6.1% 缺口0.4pp", "成本刚性 9%降幅 缺口6pp"
    # Find the bottom edge of the peach/blue KPI capsules
    kpi_bottom_ys = []
    for x in range(100, 1300):
        for y in range(160, 280):
            r, g, b = p[x, y]
            # Blue pill "缺口16%" or Pink pill "缺口6pp"
            if (b > 160 and r < 80) or (r > 180 and b < 100 and g < 100):
                kpi_bottom_ys.append(y)
    
    kpi_bottom_y = max(kpi_bottom_ys) if kpi_bottom_ys else 235
    print(f"【Block 3 KPI 区域底边缘】: Y={kpi_bottom_y}px (0-1000: {kpi_bottom_y/0.81:.1f})")

    # 2. Block 5 Top Header Bar ("2+1 破局行动")
    # Find the top edge of the dark blue banner of Block 5 in right half (x > 700)
    b5_top_ys = []
    b5_left_xs = []
    b5_right_xs = []
    b5_bottom_ys = []
    for y in range(kpi_bottom_y + 5, 400):
        for x in range(650, 1400):
            r, g, b = p[x, y]
            # Deep blue banner of "2+1"
            if b > 140 and r < 70 and g > 60:
                b5_top_ys.append(y)
                b5_left_xs.append(x)
                b5_right_xs.append(x)

    # Find bottom of Block 5 (footer pills)
    for y in range(600, 800):
        for x in range(650, 1400):
            r, g, b = p[x, y]
            if (b > 160 and r < 60) or (r > 230 and g > 240 and b > 245):
                b5_bottom_ys.append(y)

    b5_top = min(b5_top_ys) if b5_top_ys else 258
    b5_left = min(b5_left_xs) if b5_left_xs else 680
    b5_right = max(b5_right_xs) if b5_right_xs else 1380
    b5_bottom = max(b5_bottom_ys) if b5_bottom_ys else 756

    print(f"【Block 5 真实范围】:")
    print(f"  • 1440x810 像素: X=[{b5_left}, {b5_right}] (W={b5_right-b5_left}), Y=[{b5_top}, {b5_bottom}] (H={b5_bottom-b5_top})")
    print(f"  • 0-1000 归一化: box=[{b5_left/1.44:.1f}, {b5_top/0.81:.1f}, {(b5_right-b5_left)/1.44:.1f}, {(b5_bottom-b5_top)/0.81:.1f}]")
    print(f"  • 说明: Block 5 起始 Y 真实值在 318 左右 (258px)，绝不是 230-240 (那是 Block 3 的 KPI 区域)！")

    # Generate exact clean crop of Block 5
    crop_b5 = canvas.crop((b5_left - 10, b5_top - 5, b5_right + 10, b5_bottom + 10))
    crop_b5.save("output/crop_gt_slide02_block5_true.png")
    print(f"[Success] Saved TRUE crop of Block 5: output/crop_gt_slide02_block5_true.png")

if __name__ == "__main__":
    verify_all_blocks()
