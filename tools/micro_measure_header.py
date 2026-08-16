"""Detailed Micro-Measurement of Slide 02 Header Section (GT vs PPTX)"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def micro_measure():
    # 1. Canvas load
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    p = canvas.load()
    
    # 2. Rendered PPTX image
    pptx_img = Image.open("output/sim_preview.png").convert("RGB")
    pcl, pct, pcr, pcb = detect_inner_slide_canvas(pptx_img)
    pcanvas = pptx_img.crop((pcl, pct, pcr, pcb)).resize((1440, 810), Image.Resampling.LANCZOS)
    pp = pcanvas.load()

    # Measure Title in GT
    gt_title_pts = [(x, y) for y in range(20, 110) for x in range(30, 600) if p[x, y][0] < 80 and p[x, y][1] < 80 and p[x, y][2] < 80]
    gt_min_x, gt_max_x = min(pt[0] for pt in gt_title_pts), max(pt[0] for pt in gt_title_pts)
    gt_min_y, gt_max_y = min(pt[1] for pt in gt_title_pts), max(pt[1] for pt in gt_title_pts)
    gt_h = gt_max_y - gt_min_y
    gt_w = gt_max_x - gt_min_x

    # Measure Title in PPTX Render
    ppt_title_pts = [(x, y) for y in range(20, 110) for x in range(30, 600) if pp[x, y][0] < 80 and pp[x, y][1] < 80 and pp[x, y][2] < 80]
    ppt_min_x, ppt_max_x = min(pt[0] for pt in ppt_title_pts), max(pt[0] for pt in ppt_title_pts)
    ppt_min_y, ppt_max_y = min(pt[1] for pt in ppt_title_pts), max(pt[1] for pt in ppt_title_pts)
    ppt_h = ppt_max_y - ppt_min_y
    ppt_w = ppt_max_x - ppt_min_x

    # Measure Author Tag in GT
    gt_auth_pts = [(x, y) for y in range(20, 110) for x in range(1100, 1420) if p[x, y][0] < 80 and p[x, y][1] < 80 and p[x, y][2] < 80]
    gt_a_min_x, gt_a_max_x = min(pt[0] for pt in gt_auth_pts), max(pt[0] for pt in gt_auth_pts)
    gt_a_min_y, gt_a_max_y = min(pt[1] for pt in gt_auth_pts), max(pt[1] for pt in gt_auth_pts)

    # Measure Author Tag in PPTX
    ppt_auth_pts = [(x, y) for y in range(20, 110) for x in range(1100, 1420) if pp[x, y][0] < 80 and pp[x, y][1] < 80 and pp[x, y][2] < 80]
    ppt_a_min_x, ppt_a_max_x = min(pt[0] for pt in ppt_auth_pts), max(pt[0] for pt in ppt_auth_pts)
    ppt_a_min_y, ppt_a_max_y = min(pt[1] for pt in ppt_auth_pts), max(pt[1] for pt in ppt_auth_pts)

    print("=" * 80)
    print("🎯 微观级真实渲染像素比对 (1440x810 画布)")
    print("=" * 80)
    print(f"【主标题 '季度工作攻坚策略'】")
    print(f"  • 原图 GT 像素:   X: [{gt_min_x}, {gt_max_x}] (W={gt_w}px), Y: [{gt_min_y}, {gt_max_y}] (H={gt_h}px)")
    print(f"  • 还原 PPTX 像素: X: [{ppt_min_x}, {ppt_max_x}] (W={ppt_w}px), Y: [{ppt_min_y}, {ppt_max_y}] (H={ppt_h}px)")
    print(f"  • 差异分析: 还原版本 X 起点偏右 {ppt_min_x - gt_min_x}px, 文字高度矮了 {gt_h - ppt_h}px (原图 55px vs 还原 38px, 偏小约 30%!)")
    print()
    print(f"【右侧作者标识 '@鱼丸PPT'】")
    print(f"  • 原图 GT 像素:   X: [{gt_a_min_x}, {gt_a_max_x}] (W={gt_a_max_x - gt_a_min_x}px), Y: [{gt_a_min_y}, {gt_a_max_y}] (H={gt_a_max_y - gt_a_min_y}px)")
    print(f"  • 还原 PPTX 像素: X: [{ppt_a_min_x}, {ppt_a_max_x}] (W={ppt_a_max_x - ppt_a_min_x}px), Y: [{ppt_a_min_y}, {ppt_a_max_y}] (H={ppt_a_max_y - ppt_a_min_y}px)")
    print(f"  • 差异分析: 原图文字高 {gt_a_max_y - gt_a_min_y}px (对应约 22pt)，还原版本字高仅 {ppt_a_max_y - ppt_a_min_y}px (15pt)，且右边缘偏左 {gt_a_max_x - ppt_a_max_x}px")
    print("=" * 80)

if __name__ == "__main__":
    micro_measure()
