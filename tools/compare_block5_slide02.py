"""Comprehensive Inspection and Attribute Comparison for Slide 02 - Block 5 (Strategy Action Cards)"""

import os
import sys
from PIL import Image
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def analyze_block5():
    # 1. Load Ground Truth Image & Detect Canvas
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    # Crop Block 5 region in Ground Truth (x from 680 to 1440, y from 240 to 810 in 810 scale)
    block5_gt = canvas.crop((680, 240, 1420, 780))
    os.makedirs("output", exist_ok=True)
    block5_gt.save("output/crop_gt_slide02_block5.png")

    print("=" * 80)
    print("🔬 [STAGE 1] GROUND TRUTH (原图) BLOCK 5 精准像素与几何测量")
    print("=" * 80)

    # 1.1 Outer Strategy Big Card Container
    # Outer border of Block 5 card (search around x: 680~1400, y: 250~760)
    card_pixels = []
    for y in range(250, 760):
        for x in range(680, 1420):
            r, g, b = p[x, y]
            # Card area (white background or blue header or border)
            if (r > 245 and g > 245 and b > 245) or (b > 120 and r < 80) or (b > 200 and r < 180):
                card_pixels.append((x, y))

    if card_pixels:
        min_cx, max_cx = min(pt[0] for pt in card_pixels), max(pt[0] for pt in card_pixels)
        min_cy, max_cy = min(pt[1] for pt in card_pixels), max(pt[1] for pt in card_pixels)
        cw_px, ch_px = max_cx - min_cx, max_cy - min_cy
        gt_card_box_1000 = [
            round(min_cx / w * 1000, 1),
            round(min_cy / h * 1000, 1),
            round(cw_px / w * 1000, 1),
            round(ch_px / h * 1000, 1)
        ]
        print(f"1. 战略大卡外层容器 (Outer Container):")
        print(f"   • 像素范围 (1440x810): X=[{min_cx}, {max_cx}], Y=[{min_cy}, {max_cy}], 尺寸=({cw_px}x{ch_px} px)")
        print(f"   • 0-1000 坐标: box={gt_card_box_1000}")

    # 1.2 Top Cobalt Blue Header Block
    header_pixels = [(x, y, p[x, y]) for y in range(min_cy, min_cy + 80) for x in range(min_cx, max_cx) if p[x, y][2] > 130 and p[x, y][0] < 60]
    if header_pixels:
        min_hx, max_hx = min(pt[0] for pt in header_pixels), max(pt[0] for pt in header_pixels)
        min_hy, max_hy = min(pt[1] for pt in header_pixels), max(pt[1] for pt in header_pixels)
        hw_px, hh_px = max_hx - min_hx, max_hy - min_hy
        gt_header_box_1000 = [
            round(min_hx / w * 1000, 1),
            round(min_hy / h * 1000, 1),
            round(hw_px / w * 1000, 1),
            round(hh_px / h * 1000, 1)
        ]
        print(f"\n2. 顶部深蓝标题横幅 (Header Bar):")
        print(f"   • 像素范围: X=[{min_hx}, {max_hx}], Y=[{min_hy}, {max_hy}], 尺寸=({hw_px}x{hh_px} px)")
        print(f"   • 0-1000 坐标: box={gt_header_box_1000}")

    # 1.3 Action Card 1 & Action Card 2
    # In Ground Truth, let's find the white/gray action cards inside
    # Find Action Card 1 (around y: 320~480)
    card1_pixels = [(x, y) for y in range(min_hy + hh_px + 5, min_hy + hh_px + 200) for x in range(min_cx + 10, max_cx - 10) if p[x, y][0] > 235 and p[x, y][1] > 240 and p[x, y][2] > 245]
    if card1_pixels:
        c1_min_x, c1_max_x = min(pt[0] for pt in card1_pixels), max(pt[0] for pt in card1_pixels)
        c1_min_y, c1_max_y = min(pt[1] for pt in card1_pixels), max(pt[1] for pt in card1_pixels)
        print(f"\n3. 行动卡片 1 (Action Card 1):")
        print(f"   • 像素范围: X=[{c1_min_x}, {c1_max_x}], Y=[{c1_min_y}, {c1_max_y}]")
        print(f"   • 0-1000 坐标: box=[{c1_min_x/w*1000:.1f}, {c1_min_y/h*1000:.1f}, {(c1_max_x-c1_min_x)/w*1000:.1f}, {(c1_max_y-c1_min_y)/h*1000:.1f}]")

    # 1.4 Footer Pills Area
    # Around y: 680~760
    pills_pixels = [(x, y) for y in range(max_cy - 60, max_cy) for x in range(min_cx, max_cx) if p[x, y][2] > 150 or (p[x, y][0] > 230 and p[x, y][1] > 240)]
    if pills_pixels:
        p_min_x, p_max_x = min(pt[0] for pt in pills_pixels), max(pt[0] for pt in pills_pixels)
        p_min_y, p_max_y = min(pt[1] for pt in pills_pixels), max(pt[1] for pt in pills_pixels)
        print(f"\n4. 底部关键词胶囊区 (Footer Pills Bar):")
        print(f"   • 像素范围: X=[{p_min_x}, {p_max_x}], Y=[{p_min_y}, {p_max_y}]")
        print(f"   • 0-1000 坐标: box=[{p_min_x/w*1000:.1f}, {p_min_y/h*1000:.1f}, {(p_max_x-p_min_x)/w*1000:.1f}, {(p_max_y-p_min_y)/h*1000:.1f}]")

    print("\n" + "=" * 80)
    print("📦 [STAGE 2] PPTX 文件 (OpenXML DOM) Block 5 元素属性提取")
    print("=" * 80)

    prs = Presentation("output/slide_02.pptx")
    slide = prs.slides[0]
    sw, sh = prs.slide_width, prs.slide_height

    for idx, shape in enumerate(slide.shapes):
        l = round((shape.left / sw) * 1000.0, 1)
        t = round((shape.top / sh) * 1000.0, 1)
        w_ = round((shape.width / sw) * 1000.0, 1)
        h_ = round((shape.height / sh) * 1000.0, 1)

        # Block 5 is in l >= 470, t >= 300
        if l >= 470 and t >= 300:
            text = shape.text_frame.text.replace("\n", " | ") if shape.has_text_frame else ""
            align = "left"
            font_size = None
            bold = False
            if shape.has_text_frame and shape.text_frame.paragraphs:
                p0 = shape.text_frame.paragraphs[0]
                if p0.alignment == 2: align = "center"
                elif p0.alignment == 3: align = "right"
                if p0.runs:
                    font_size = p0.runs[0].font.size.pt if p0.runs[0].font.size else None
                    bold = p0.runs[0].font.bold or False

            fill = f"#{shape.fill.fore_color.rgb}" if shape.fill and shape.fill.type == 1 and shape.fill.fore_color and shape.fill.fore_color.rgb else "gradient/none"
            print(f"  • Shape #{idx+1:02d} ({shape.name:<20}): box=[{l:5.1f}, {t:5.1f}, {w_:5.1f}, {h_:5.1f}] | text='{text[:35]:<35}' | align={align} | font_size={str(font_size)+'pt':<7} | bold={str(bold):<5}")

    # Generate Block 5 diff
    os.system(".venv/bin/python tools/render_and_diff.py output/slide_02.pptx input/slide_02.png --crop-box 475 310 505 620 --block-title 'Block 5: Strategy Action Card' -o output/diff_block5_slide02.png")

if __name__ == "__main__":
    analyze_block5()
