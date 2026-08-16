"""Comprehensive Inspection and Attribute Comparison for Slide 02 - Block 1 (Header)"""

import os
import sys
from PIL import Image, ImageStat
from pptx import Presentation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas, render_pptx_to_image, compare_and_generate_diff

def analyze_block1():
    # 1. Load Ground Truth Image & Detect Canvas
    raw_img = Image.open("input/slide_02.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size
    p = canvas.load()

    # Crop Block 1 area for visual inspection
    # Block 1 region: y from 0 to 110 in 810 scale (0 to 135 in 0-1000)
    block1_gt = canvas.crop((0, 0, 1440, 105))
    os.makedirs("output", exist_ok=True)
    block1_gt.save("output/crop_gt_slide02_block1.png")

    print("=" * 80)
    print("🔬 [STAGE 1] GROUND TRUTH (原图) BLOCK 1 精准像素与几何测量")
    print("=" * 80)

    # 1.1 Find Main Title "季度工作攻坚策略"
    title_pixels = []
    for y in range(15, 90):
        for x in range(30, 600):
            r, g, b = p[x, y]
            # Title is dark / black (R, G, B < 80)
            if r < 80 and g < 80 and b < 80:
                title_pixels.append((x, y, (r, g, b)))

    gt_title_box_px = []
    gt_title_box_1000 = []
    title_font_pt = 0
    title_color = "#000000"
    if title_pixels:
        min_tx = min(pt[0] for pt in title_pixels)
        max_tx = max(pt[0] for pt in title_pixels)
        min_ty = min(pt[1] for pt in title_pixels)
        max_ty = max(pt[1] for pt in title_pixels)
        gt_title_box_px = [min_tx, min_ty, max_tx - min_tx, max_ty - min_ty]
        gt_title_box_1000 = [
            round(min_tx / w * 1000, 1),
            round(min_ty / h * 1000, 1),
            round((max_tx - min_tx) / w * 1000, 1),
            round((max_ty - min_ty) / h * 1000, 1)
        ]
        h_px = max_ty - min_ty
        # Em square conversion: font_size ≈ h_px * 0.667 / 0.82
        title_font_pt = round((h_px * 0.667) / 0.82, 1)
        # Sample color from darkest central pixels
        darkest = min(title_pixels, key=lambda pt: sum(pt[2]))[2]
        title_color = f"#{darkest[0]:02X}{darkest[1]:02X}{darkest[2]:02X}"

        print(f"1. 主标题 (Title):")
        print(f"   • 像素范围 (1440x810): X=[{min_tx}, {max_tx}], Y=[{min_ty}, {max_ty}], 尺寸=({max_tx-min_tx}x{h_px} px)")
        print(f"   • 0-1000 坐标: box={gt_title_box_1000}")
        print(f"   • 测得字符像素高: {h_px} px -> 理论字号: {title_font_pt} pt (对应字阶: ~26-28 pt)")
        print(f"   • 对齐方式: 靠左对齐 (Left), 左边距: {gt_title_box_1000[0]}")
        print(f"   • 测得颜色: {title_color}")

    # 1.2 Find Divider Line
    line_pixels = []
    for y in range(50, 95):
        for x in range(30, 1400):
            r, g, b = p[x, y]
            # Divider line is light gray / blue-gray (190 < r,g,b < 230)
            if 180 < r < 235 and 180 < g < 235 and 180 < b < 235 and abs(r - g) < 15 and abs(g - b) < 15:
                # Check if it forms a continuous horizontal line
                line_pixels.append((x, y, (r, g, b)))

    gt_line_box_1000 = []
    line_color = "#CBD5E1"
    line_thickness_pt = 1.0
    if line_pixels:
        # Group by Y to find the most populated line
        y_counts = {}
        for x, y, c in line_pixels:
            y_counts[y] = y_counts.get(y, 0) + 1
        best_y = max(y_counts, key=y_counts.get)
        line_xs = [pt[0] for pt in line_pixels if abs(pt[1] - best_y) <= 1]
        if line_xs:
            min_lx, max_lx = min(line_xs), max(line_xs)
            gt_line_box_1000 = [
                round(min_lx / w * 1000, 1),
                round(best_y / h * 1000, 1),
                round((max_lx - min_lx) / w * 1000, 1),
                round(1.5 / 0.81, 1)
            ]
            c_samples = [pt[2] for pt in line_pixels if pt[1] == best_y]
            avg_c = tuple(sum(col[i] for col in c_samples)//len(c_samples) for i in range(3))
            line_color = f"#{avg_c[0]:02X}{avg_c[1]:02X}{avg_c[2]:02X}"
            print(f"\n2. 下划分割线 (Divider Line):")
            print(f"   • 0-1000 坐标: [left={gt_line_box_1000[0]}, top={gt_line_box_1000[1]}, width={gt_line_box_1000[2]}]")
            print(f"   • 测得颜色: {line_color}")

    # 1.3 Find Right Author Tag
    author_pixels = []
    for y in range(15, 80):
        for x in range(1000, 1420):
            r, g, b = p[x, y]
            if r < 120 and g < 120 and b < 120:
                author_pixels.append((x, y, (r, g, b)))

    gt_author_box_1000 = []
    author_font_pt = 0
    author_color = "#181818"
    if author_pixels:
        min_ax = min(pt[0] for pt in author_pixels)
        max_ax = max(pt[0] for pt in author_pixels)
        min_ay = min(pt[1] for pt in author_pixels)
        max_ay = max(pt[1] for pt in author_pixels)
        gt_author_box_1000 = [
            round(min_ax / w * 1000, 1),
            round(min_ay / h * 1000, 1),
            round((max_ax - min_ax) / w * 1000, 1),
            round((max_ay - min_ay) / h * 1000, 1)
        ]
        ah_px = max_ay - min_ay
        author_font_pt = round((ah_px * 0.667) / 0.82, 1)
        darkest_a = min(author_pixels, key=lambda pt: sum(pt[2]))[2]
        author_color = f"#{darkest_a[0]:02X}{darkest_a[1]:02X}{darkest_a[2]:02X}"

        print(f"\n3. 右侧作者标识 (Author Tag):")
        print(f"   • 0-1000 坐标: box={gt_author_box_1000}")
        print(f"   • 测得字符像素高: {ah_px} px -> 理论字号: {author_font_pt} pt (对应字阶: ~13-15 pt)")
        print(f"   • 对齐方式: 靠右对齐 (Right), 右边距: {round(1000 - (gt_author_box_1000[0] + gt_author_box_1000[2]), 1)}")
        print(f"   • 测得颜色: {author_color}")

    print("\n" + "=" * 80)
    print("📦 [STAGE 2] PPTX 文件 (OpenXML DOM) 真实属性提取")
    print("=" * 80)

    prs = Presentation("output/slide_02.pptx")
    slide = prs.slides[0]
    sw, sh = prs.slide_width, prs.slide_height

    pptx_b1_elements = []
    for idx, shape in enumerate(slide.shapes):
        l = round((shape.left / sw) * 1000.0, 1)
        t = round((shape.top / sh) * 1000.0, 1)
        w_ = round((shape.width / sw) * 1000.0, 1)
        h_ = round((shape.height / sh) * 1000.0, 1)

        # We care about Block 1 elements (top <= 100)
        if t <= 100:
            text = ""
            font_size = None
            bold = False
            align = "left"
            font_color = None
            fill_color = None

            if shape.has_text_frame:
                tf = shape.text_frame
                text = tf.text.strip()
                if tf.paragraphs:
                    p0 = tf.paragraphs[0]
                    if p0.alignment == 2:
                        align = "center"
                    elif p0.alignment == 3:
                        align = "right"
                    elif p0.alignment == 1:
                        align = "left"
                    if p0.runs:
                        r0 = p0.runs[0]
                        font_size = r0.font.size.pt if r0.font.size else None
                        bold = r0.font.bold or False
                        if r0.font.color and r0.font.color.rgb:
                            font_color = f"#{r0.font.color.rgb}"

            try:
                if shape.fill and shape.fill.type == 1:
                    fill_color = f"#{shape.fill.fore_color.rgb}"
            except Exception:
                pass

            elem = {
                "id": idx + 1,
                "name": shape.name,
                "box": [l, t, w_, h_],
                "text": text,
                "font_size": font_size,
                "bold": bold,
                "align": align,
                "font_color": font_color,
                "fill_color": fill_color,
            }
            pptx_b1_elements.append(elem)
            print(f"  • Shape #{idx+1} ({shape.name}):")
            print(f"    - box: {elem['box']}")
            print(f"    - text: '{elem['text']}'")
            print(f"    - font_size: {elem['font_size']} pt, bold: {elem['bold']}, align: {elem['align']}, color: {elem['font_color']}, fill: {elem['fill_color']}")

    # 3. Render Block 1 slice diff
    render_and_diff_b1()

def render_and_diff_b1():
    print("\n" + "=" * 80)
    print("🎨 [STAGE 3] 生成 Block 1 局部切片比对图 (Slice Diff)")
    print("=" * 80)
    # Block 1 crop box: [30, 20, 940, 85]
    os.system(".venv/bin/python tools/render_and_diff.py output/slide_02.pptx input/slide_02.png --crop-box 30 20 940 85 --block-title 'Block 1: Header Section' -o output/diff_block1_slide02.png")

if __name__ == "__main__":
    analyze_block1()
