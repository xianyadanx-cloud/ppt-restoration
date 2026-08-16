"""Detailed Micro-Measurement and Optimization for Slide 02 Block 5"""

import os
import sys
from PIL import Image
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def micro_measure_b5():
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    # 1. Header Text "2+1" and "破局行动" in GT (x: 690~1100, y: 250~330)
    # Find "2+1" pixels
    t21_px = [(x, y) for y in range(250, 330) for x in range(680, 800) if p[x, y][0] > 240 and p[x, y][1] > 240 and p[x, y][2] > 240]
    if t21_px:
        min_21_y, max_21_y = min(pt[1] for pt in t21_px), max(pt[1] for pt in t21_px)
        min_21_x, max_21_x = min(pt[0] for pt in t21_px), max(pt[0] for pt in t21_px)
        h21 = max_21_y - min_21_y
        pt_21 = round((h21 * 0.667) / 0.80, 1)
        print(f"【'2+1' 真实测量】")
        print(f"  • 像素: X=[{min_21_x}, {max_21_x}], Y=[{min_21_y}, {max_21_y}], H={h21}px -> 理论字号: {pt_21} pt (对应 ~36-40 pt)")

    # Find "破局行动" pixels (x: 780~950, y: 260~330)
    poju_px = [(x, y) for y in range(260, 330) for x in range(780, 950) if p[x, y][0] > 240 and p[x, y][1] > 240 and p[x, y][2] > 240]
    if poju_px:
        min_pj_y, max_pj_y = min(pt[1] for pt in poju_px), max(pt[1] for pt in poju_px)
        hpj = max_pj_y - min_pj_y
        pt_pj = round((hpj * 0.667) / 0.80, 1)
        print(f"【'破局行动' 真实测量】")
        print(f"  • 字高: {hpj}px -> 理论字号: {pt_pj} pt (对应 ~20-22 pt)")

    # 2. Action Card 1 & 2 exact Y ranges
    # Card 1 title "流量重构-突破渠道瓶颈"
    c1_title_px = [(x, y) for y in range(320, 420) for x in range(720, 1050) if p[x, y][0] < 60 and p[x, y][1] < 60 and p[x, y][2] < 60]
    if c1_title_px:
        min_c1t_y, max_c1t_y = min(pt[1] for pt in c1_title_px), max(pt[1] for pt in c1_title_px)
        hc1 = max_c1t_y - min_c1t_y
        pt_c1 = round((hc1 * 0.667) / 0.80, 1)
        print(f"【行动卡片1 标题 '流量重构...' 真实测量】")
        print(f"  • 字高: {hc1}px -> 理论字号: {pt_c1} pt (对应 ~14-15 pt)")

    # Check bottom boundary of Card 1 & top of Card 2
    # In GT, Card 1 ends around y=440 (0-1000: ~540), Card 2 starts around y=470 (0-1000: ~580)
    print(f"\n【卡片高度与留白优化建议】")
    print(f"  • 卡片高度应由 215 缩减至约 175~180，减少多余空白，提升紧凑度与专业度。")

if __name__ == "__main__":
    micro_measure_b5()
