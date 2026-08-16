"""Detailed Micro-Measurement of Slide 02 Block 2 (Summary Banner)"""

import os
import sys
from PIL import Image
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def micro_measure_b2():
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    # 1. Left container edge & right container edge
    # Outer light blue card boundary
    card_x = [x for x in range(20, 1420) if p[x, 130][2] > 240 or (p[x, 130][2] > 140 and p[x, 130][0] < 80)]
    min_cx, max_cx = min(card_x), max(card_x)
    card_y = [y for y in range(85, 180) if p[500, y][2] > 240 and p[500, y][0] > 220]
    min_cy, max_cy = min(card_y), max(card_y)

    print(f"【外层底卡容器真实几何】")
    print(f"  • 1440x810 像素: X=[{min_cx}, {max_cx}] (W={max_cx-min_cx}px), Y=[{min_cy}, {max_cy}] (H={max_cy-min_cy}px)")
    print(f"  • 0-1000 坐标: [{min_cx/1.44:.1f}, {min_cy/0.81:.1f}, {(max_cx-min_cx)/1.44:.1f}, {(max_cy-min_cy)/0.81:.1f}]")

    # 2. Left Blue Badge boundary
    badge_x = [x for x in range(min_cx, min_cx + 200) if p[x, int((min_cy+max_cy)/2)][2] > 140 and p[x, int((min_cy+max_cy)/2)][0] < 80]
    min_gx, max_gx = min(badge_x), max(badge_x)
    print(f"【左侧深蓝徽章真实几何】")
    print(f"  • 1440x810 像素: X=[{min_gx}, {max_gx}] (W={max_gx-min_gx}px)")
    print(f"  • 0-1000 坐标: [{min_gx/1.44:.1f}, {min_cy/0.81:.1f}, {(max_gx-min_gx)/1.44:.1f}, {(max_cy-min_cy)/0.81:.1f}]")

    # 3. Text start X & end X
    text_x = [x for x in range(max_gx + 5, max_cx) for y in range(min_cy, max_cy) if p[x, y][0] < 90 and p[x, y][1] < 90 and p[x, y][2] < 90]
    min_tx, max_tx = min(text_x), max(text_x)
    print(f"【右侧文字区域真实几何】")
    print(f"  • 1440x810 像素: X=[{min_tx}, {max_tx}] (W={max_tx-min_tx}px)")
    print(f"  • 0-1000 坐标: [{min_tx/1.44:.1f}, {min_cy/0.81:.1f}, {(max_tx-min_tx)/1.44:.1f}, {(max_cy-min_cy)/0.81:.1f}]")

if __name__ == "__main__":
    micro_measure_b2()
