"""Comprehensive Inspection and Attribute Comparison for Slide 02 - Block 2 (Summary Banner)"""

import os
import sys
from PIL import Image, ImageStat
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

def analyze_block2():
    # 1. Load Ground Truth Image & Detect Canvas
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    # Crop Block 2 region in Ground Truth (y from 80 to 180 in 810 scale)
    block2_gt = canvas.crop((0, 75, 1440, 175))
    os.makedirs("output", exist_ok=True)
    block2_gt.save("output/crop_gt_slide02_block2.png")

    print("=" * 80)
    print("🔬 [STAGE 1] GROUND TRUTH (原图) BLOCK 2 精准像素与几何测量")
    print("=" * 80)

    # 1.1 Outer Banner Container (Light Blue Background)
    # Search for light blue background pixels around y=90~150, x=30~1400
    banner_pixels = []
    for y in range(80, 165):
        for x in range(25, 1420):
            r, g, b = p[x, y]
            # Light blue container background (typically R:230-245, G:240-250, B:250-255)
            # or Left Badge blue (B > 130, R < 60)
            if (220 < r < 248 and 230 < g < 252 and 240 < b < 255) or (b > 130 and r < 70):
                banner_pixels.append((x, y))

    if banner_pixels:
        min_bx, max_bx = min(pt[0] for pt in banner_pixels), max(pt[0] for pt in banner_pixels)
        min_by, max_by = min(pt[1] for pt in banner_pixels), max(pt[1] for pt in banner_pixels)
        bw_px = max_bx - min_bx
        bh_px = max_by - min_by
        gt_banner_box_1000 = [
            round(min_bx / w * 1000, 1),
            round(min_by / h * 1000, 1),
            round(bw_px / w * 1000, 1),
            round(bh_px / h * 1000, 1)
        ]
        # Sample bg color
        bg_r, bg_g, bg_b = p[int(min_bx + 150), int(min_by + bh_px / 2)]
        print(f"1. 外层浅蓝底卡容器 (Outer Container):")
        print(f"   • 像素范围 (1440x810): X=[{min_bx}, {max_bx}], Y=[{min_by}, {max_by}], 尺寸=({bw_px}x{bh_px} px)")
        print(f"   • 0-1000 坐标: box={gt_banner_box_1000}")
        print(f"   • 测得背景色: #{bg_r:02X}{bg_g:02X}{bg_b:02X} (RGB: {bg_r}, {bg_g}, {bg_b})")

    # 1.2 Left Deep Blue Badge "总览概述"
    badge_pixels = []
    for y in range(80, 165):
        for x in range(25, 300):
            r, g, b = p[x, y]
            # Deep blue badge: b > 140, r < 60, g > 60
            if b > 130 and r < 60 and g > 60:
                badge_pixels.append((x, y, (r, g, b)))

    if badge_pixels:
        min_gx, max_gx = min(pt[0] for pt in badge_pixels), max(pt[0] for pt in badge_pixels)
        min_gy, max_gy = min(pt[1] for pt in badge_pixels), max(pt[1] for pt in badge_pixels)
        gw_px = max_gx - min_gx
        gh_px = max_gy - min_gy
        gt_badge_box_1000 = [
            round(min_gx / w * 1000, 1),
            round(min_gy / h * 1000, 1),
            round(gw_px / w * 1000, 1),
            round(gh_px / h * 1000, 1)
        ]
        # Check badge top color vs bottom color
        top_c = [pt[2] for pt in badge_pixels if pt[1] == min_gy + 5]
        bot_c = [pt[2] for pt in badge_pixels if pt[1] == max_gy - 5]
        avg_top = tuple(sum(col[i] for col in top_c)//len(top_c) for i in range(3)) if top_c else (27, 100, 184)
        avg_bot = tuple(sum(col[i] for col in bot_c)//len(bot_c) for i in range(3)) if bot_c else (46, 123, 217)

        print(f"\n2. 左侧深蓝徽章 (Left Gradient Badge):")
        print(f"   • 像素范围: X=[{min_gx}, {max_gx}], Y=[{min_gy}, {max_gy}], 尺寸=({gw_px}x{gh_px} px)")
        print(f"   • 0-1000 坐标: box={gt_badge_box_1000}")
        print(f"   • 顶部颜色: #{avg_top[0]:02X}{avg_top[1]:02X}{avg_top[2]:02X}, 底部颜色: #{avg_bot[0]:02X}{avg_bot[1]:02X}{avg_bot[2]:02X}")

    # 1.3 Badge Text "总览\n概述"
    badge_text_px = []
    for y in range(min_gy, max_gy):
        for x in range(min_gx, max_gx):
            r, g, b = p[x, y]
            # White text: r, g, b > 230
            if r > 225 and g > 225 and b > 225:
                badge_text_px.append((x, y))

    if badge_text_px:
        b_tx_min, b_tx_max = min(pt[0] for pt in badge_text_px), max(pt[0] for pt in badge_text_px)
        b_ty_min, b_ty_max = min(pt[1] for pt in badge_text_px), max(pt[1] for pt in badge_text_px)
        # Split into two lines by Y gap
        y_hist = {}
        for x, y in badge_text_px:
            y_hist[y] = y_hist.get(y, 0) + 1
        line1_pts = [pt for pt in badge_text_px if pt[1] < (b_ty_min + b_ty_max) / 2]
        line2_pts = [pt for pt in badge_text_px if pt[1] >= (b_ty_min + b_ty_max) / 2]
        h1 = (max(pt[1] for pt in line1_pts) - min(pt[1] for pt in line1_pts)) if line1_pts else 15
        badge_font_pt = round((h1 * 0.667) / 0.80, 1)
        print(f"   • 徽章文字 '总览概述': 测得单行字高: {h1} px -> 理论字号: {badge_font_pt} pt (对应 ~14-16 pt, Bold, Center)")

    # 1.4 Right Rich Text (Summary Body Text)
    body_text_px = []
    for y in range(min_by, max_by):
        for x in range(max_gx + 10, max_bx):
            r, g, b = p[x, y]
            # Dark text in body: r < 100, g < 100, b < 100
            if r < 100 and g < 100 and b < 100:
                body_text_px.append((x, y, (r, g, b)))

    if body_text_px:
        min_bx2, max_bx2 = min(pt[0] for pt in body_text_px), max(pt[0] for pt in body_text_px)
        min_by2, max_by2 = min(pt[1] for pt in body_text_px), max(pt[1] for pt in body_text_px)
        # Find lines in body text
        y_counts = {}
        for x, y, c in body_text_px:
            y_counts[y] = y_counts.get(y, 0) + 1
        # Detect line heights
        sorted_ys = sorted([y for y, count in y_counts.items() if count > 15])
        # Find lines clusters
        lines = []
        curr_line = []
        for y in sorted_ys:
            if not curr_line or y - curr_line[-1] <= 3:
                curr_line.append(y)
            else:
                lines.append(curr_line)
                curr_line = [y]
        if curr_line:
            lines.append(curr_line)

        print(f"\n3. 右侧正文描述 (Right Body Text):")
        print(f"   • 像素范围: X=[{min_bx2}, {max_bx2}], Y=[{min_by2}, {max_by2}]")
        print(f"   • 0-1000 坐标: box=[{min_bx2/w*1000:.1f}, {min_by2/h*1000:.1f}, {(max_bx2-min_bx2)/w*1000:.1f}, {(max_by2-min_by2)/h*1000:.1f}]")
        print(f"   • 检测到文本行数: {len(lines)} 行")
        for idx, l_ys in enumerate(lines):
            lh = max(l_ys) - min(l_ys)
            l_pt = round((lh * 0.667) / 0.80, 1)
            print(f"     - 第 {idx+1} 行 Y=[{min(l_ys)}, {max(l_ys)}], 高度={lh}px -> 理论字号: {l_pt} pt (对应 ~11-12 pt)")

    print("\n" + "=" * 80)
    print("📦 [STAGE 2] PPTX 文件 (OpenXML DOM) 真实属性提取")
    print("=" * 80)

    prs = Presentation("output/slide_02.pptx")
    slide = prs.slides[0]
    sw, sh = prs.slide_width, prs.slide_height

    for idx, shape in enumerate(slide.shapes):
        l = round((shape.left / sw) * 1000.0, 1)
        t = round((shape.top / sh) * 1000.0, 1)
        w_ = round((shape.width / sw) * 1000.0, 1)
        h_ = round((shape.height / sh) * 1000.0, 1)

        # Block 2 shapes are in top 100~190
        if 100 <= t <= 185 and l <= 150:
            text = shape.text_frame.text.replace("\n", " ") if shape.has_text_frame else ""
            align = "left"
            font_size = None
            if shape.has_text_frame and shape.text_frame.paragraphs:
                p0 = shape.text_frame.paragraphs[0]
                if p0.alignment == 2: align = "center"
                elif p0.alignment == 3: align = "right"
                if p0.runs:
                    font_size = p0.runs[0].font.size.pt if p0.runs[0].font.size else None
            
            fill = f"#{shape.fill.fore_color.rgb}" if shape.fill and shape.fill.type == 1 and shape.fill.fore_color and shape.fill.fore_color.rgb else "gradient/none"
            print(f"  • Shape #{idx+1} ({shape.name}): box=[{l}, {t}, {w_}, {h_}] | text='{text[:30]}' | align={align} | font_size={font_size} pt | fill={fill}")

    # Generate current Block 2 diff
    os.system(".venv/bin/python tools/render_and_diff.py output/slide_02.pptx input/slide_02.png --crop-box 20 100 960 85 --block-title 'Block 2: Summary Banner' -o output/diff_block2_slide02.png")

if __name__ == "__main__":
    analyze_block2()
