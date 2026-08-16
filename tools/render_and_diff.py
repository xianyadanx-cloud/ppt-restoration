"""Enhanced render_and_diff with True Linear Gradients and High-Fidelity Bold Font Rendering."""

import os
import sys
import math
import argparse
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE


def hex_to_rgb(hex_str):
    if not hex_str or hex_str.lower() == "transparent":
        return None
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))
    return (0, 0, 0)


def extract_gradient_colors(shape_element):
    """Extract start and end colors from DrawingML gradFill."""
    gradFill = shape_element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}gradFill")
    if gradFill is not None:
        gsLst = gradFill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}gsLst")
        if gsLst is not None:
            colors = []
            for gs in gsLst.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}gs"):
                srgbClr = gs.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                if srgbClr is not None:
                    val = srgbClr.attrib.get("val")
                    if val:
                        colors.append(hex_to_rgb(val))
            if len(colors) >= 2:
                return colors[0], colors[-1]
    return None


def detect_inner_slide_canvas(img: Image.Image) -> Tuple[int, int, int, int]:
    """Detect the actual white/light slide bounding box within a screenshot with gray bezels."""
    w, h = img.size
    top_edge, bottom_edge, left_edge, right_edge = 0, h - 1, 0, w - 1

    # Top
    for y in range(0, h // 3):
        row = [img.getpixel((x, y)) for x in range(w // 4, 3 * w // 4, 10)]
        if sum(p[0] + p[1] + p[2] for p in row) / (3 * len(row)) > 240:
            top_edge = y
            break

    # Bottom
    for y in range(h - 1, 2 * h // 3, -1):
        row = [img.getpixel((x, y)) for x in range(w // 4, 3 * w // 4, 10)]
        if sum(p[0] + p[1] + p[2] for p in row) / (3 * len(row)) > 240:
            bottom_edge = y
            break

    # Left
    for x in range(0, w // 4):
        col = [img.getpixel((x, y)) for y in range(h // 4, 3 * h // 4, 10)]
        if sum(p[0] + p[1] + p[2] for p in col) / (3 * len(col)) > 240:
            left_edge = x
            break

    # Right
    for x in range(w - 1, 3 * w // 4, -1):
        col = [img.getpixel((x, y)) for y in range(h // 4, 3 * h // 4, 10)]
        if sum(p[0] + p[1] + p[2] for p in col) / (3 * len(col)) > 240:
            right_edge = x
            break

    # If image is already exact 16:9 ratio (e.g. 1440x810, 1920x1080) and not an uncropped screenshot
    if abs(w / h - 16.0 / 9.0) < 0.01:
        # Check if top-left and top-right are clean slide background
        corners = [img.getpixel((0, 0)), img.getpixel((w - 1, 0)), img.getpixel((0, h - 1)), img.getpixel((w - 1, h - 1))]
        avg_corner = sum(p[0] + p[1] + p[2] for p in corners) / (4 * 3)
        if avg_corner > 220:  # already clean canvas
            return 0, 0, w, h

    if (right_edge - left_edge > w * 0.7) and (bottom_edge - top_edge > h * 0.7):
        return left_edge, top_edge, right_edge, bottom_edge
    return 0, 0, w, h


def draw_linear_gradient(
    target_img: Image.Image,
    box: List[int],
    c0: Tuple[int, int, int],
    c1: Tuple[int, int, int],
    radius: int = 0,
    outline_color: Optional[Tuple[int, int, int]] = None,
    outline_width: int = 1,
) -> None:
    """Draw a smooth vertical linear gradient with optional corner radius."""
    x0, y0, x1, y1 = box
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    # Generate vertical gradient strip
    grad_img = Image.new("RGBA", (w, h))
    pixels = grad_img.load()
    for y in range(h):
        t = y / float(h - 1) if h > 1 else 0.0
        r = int(c0[0] * (1 - t) + c1[0] * t)
        g = int(c0[1] * (1 - t) + c1[1] * t)
        b = int(c0[2] * (1 - t) + c1[2] * t)
        for x in range(w):
            pixels[x, y] = (r, g, b, 255)

    # Optional Mask for Rounded Corners
    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
        target_img.paste(grad_img, (x0, y0), mask)
        if outline_color:
            draw = ImageDraw.Draw(target_img)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(outline_color[0], outline_color[1], outline_color[2], 255), width=outline_width)
    else:
        target_img.paste(grad_img, (x0, y0))
        if outline_color:
            draw = ImageDraw.Draw(target_img)
            draw.rectangle([x0, y0, x1, y1], outline=(outline_color[0], outline_color[1], outline_color[2], 255), width=outline_width)


def render_pptx_to_image(pptx_path, out_img_path, target_size=(1440, 810)):
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    sw = prs.slide_width
    sh = prs.slide_height
    tw, th = target_size

    # Background
    img = Image.new("RGBA", (tw, th), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Font setup
    pt_scale = th / 540.0

    def get_font(size_pt, bold=False):
        scaled_size = max(10, int(size_pt * pt_scale))
        try:
            if bold:
                # STHeiti Medium / Hiragino W6
                if os.path.exists("/System/Library/Fonts/STHeiti Medium.ttc"):
                    return ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", scaled_size)
                elif os.path.exists("/System/Library/Fonts/Hiragino Sans GB.ttc"):
                    return ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", scaled_size, index=1)
            else:
                if os.path.exists("/System/Library/Fonts/Hiragino Sans GB.ttc"):
                    return ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", scaled_size, index=0)
                elif os.path.exists("/System/Library/Fonts/STHeiti Light.ttc"):
                    return ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", scaled_size)
        except Exception:
            pass
        return ImageFont.load_default()

    # Iterate through shapes
    for shape in slide.shapes:
        l = int((shape.left / sw) * tw)
        t = int((shape.top / sh) * th)
        w = int((shape.width / sw) * tw)
        h = int((shape.height / sh) * th)
        r = l + w
        b = t + h

        # Determine Fill & Line colors
        fill_color = None
        line_color = None
        grad_colors = extract_gradient_colors(shape._element) if hasattr(shape, "_element") and hasattr(shape._element, "spPr") else None

        try:
            if shape.fill and shape.fill.type == 1:  # SOLID
                c = shape.fill.fore_color.rgb
                fill_color = (c[0], c[1], c[2], 255)
        except Exception:
            pass

        try:
            if shape.line and shape.line.color and shape.line.color.rgb:
                c = shape.line.color.rgb
                line_color = (c[0], c[1], c[2], 255)
        except Exception:
            pass

        # 1. FREEFORM POLYGON (shape_type == 5)
        if shape.shape_type == 5:
            custGeom = shape._element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}custGeom")
            if custGeom is not None:
                pathLst = custGeom.find("{http://schemas.openxmlformats.org/drawingml/2006/main}pathLst")
                if pathLst is not None:
                    for path in pathLst.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}path"):
                        pw = float(path.attrib.get("w", 1))
                        ph = float(path.attrib.get("h", 1))
                        poly_pts = []
                        for elem in path:
                            pt = elem.find("{http://schemas.openxmlformats.org/drawingml/2006/main}pt")
                            if pt is not None:
                                px = float(pt.attrib.get("x", 0))
                                py = float(pt.attrib.get("y", 0))
                                abs_x = l + (px / pw) * w
                                abs_y = t + (py / ph) * h
                                poly_pts.append((abs_x, abs_y))
                        if len(poly_pts) >= 3:
                            draw.polygon(poly_pts, fill=fill_color or (50, 100, 200, 255), outline=line_color)

        # 2. AUTO_SHAPE (shape_type == 1)
        elif shape.shape_type == 1:
            if grad_colors and len(grad_colors) >= 2:
                radius = 8 if shape.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE else 0
                draw_linear_gradient(img, [l, t, r, b], grad_colors[0], grad_colors[1], radius=radius, outline_color=line_color)
            elif shape.auto_shape_type == MSO_SHAPE.OVAL:
                draw.ellipse([l, t, r, b], fill=fill_color, outline=line_color, width=1 if line_color else 0)
            elif shape.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
                radius = min(12, max(4, int(min(w, h) * 0.25)))
                draw.rounded_rectangle([l, t, r, b], radius=radius, fill=fill_color, outline=line_color, width=1 if line_color else 0)
            else:
                draw.rectangle([l, t, r, b], fill=fill_color, outline=line_color, width=1 if line_color else 0)

        # 3. TABLE SHAPE
        elif shape.has_table:
            table = shape.table
            num_rows = len(table.rows)
            num_cols = len(table.columns)
            
            col_widths_px = [(col.width / sw) * tw for col in table.columns]
            sum_row_h = sum(row.height for row in table.rows)
            if sum_row_h > 0 and abs((sum_row_h / sh) * th - h) > 5:
                row_heights_px = [(row.height / sum_row_h) * h for row in table.rows]
            else:
                row_heights_px = [h / num_rows for _ in table.rows]
            
            cur_y = t
            for row_idx, row in enumerate(table.rows):
                cur_h = row_heights_px[row_idx]
                cur_x = l
                for col_idx, cell in enumerate(row.cells):
                    cur_w = col_widths_px[col_idx] if col_idx < len(col_widths_px) else (w / num_cols)
                    cell_box = [cur_x, cur_y, cur_x + cur_w, cur_y + cur_h]
                    
                    cell_fill = None
                    try:
                        if cell.fill and cell.fill.type == 1:
                            cf = cell.fill.fore_color.rgb
                            cell_fill = (cf[0], cf[1], cf[2], 255)
                    except Exception:
                        pass
                    
                    if cell_fill:
                        draw.rectangle(cell_box, fill=cell_fill)
                    
                    # Draw cell text
                    cell_text = cell.text.strip()
                    if cell_text:
                        p_text = cell.text_frame.text
                        fnt = get_font(11, bold=(row_idx == 0))
                        tc = (255, 255, 255, 255) if row_idx == 0 else (51, 65, 85, 255)
                        
                        bbox = draw.textbbox((0, 0), p_text, font=fnt)
                        tw_t = bbox[2] - bbox[0]
                        th_t = bbox[3] - bbox[1]
                        
                        align_x = cur_x + (cur_w - tw_t) / 2
                        align_y = cur_y + (cur_h - th_t) / 2
                        draw.text((align_x, align_y), p_text, fill=tc, font=fnt)
                    
                    cur_x += cur_w
                cur_y += cur_h

        # 4. TEXT FRAMES
        if shape.has_text_frame and not shape.has_table:
            tf = shape.text_frame
            for p_idx, p in enumerate(tf.paragraphs):
                p_text = p.text
                if not p_text.strip():
                    continue
                
                # Check runs
                if p.runs:
                    # Estimate line width for centering
                    total_p_w = 0
                    for r in p.runs:
                        r_sz = r.font.size.pt if r.font.size else 11
                        r_bold = r.font.bold or False
                        f_tmp = get_font(r_sz, bold=r_bold)
                        bb = draw.textbbox((0, 0), r.text, font=f_tmp)
                        total_p_w += bb[2] - bb[0]
                    
                    if p.alignment == 2:  # Center
                        start_x = l + max(0, (w - total_p_w) / 2)
                    elif p.alignment == 3:  # Right
                        start_x = l + max(0, w - total_p_w - 8)
                    else:
                        start_x = l + 4
                    
                    cur_x = start_x
                    cur_y = t + 2 + p_idx * 20
                    max_right = l + w - 4
                    
                    for run in p.runs:
                        r_sz = run.font.size.pt if run.font.size else 11
                        r_bold = run.font.bold or False
                        r_col = (15, 23, 42, 255)
                        if run.font.color and run.font.color.rgb:
                            rc = run.font.color.rgb
                            r_col = (rc[0], rc[1], rc[2], 255)
                        fnt = get_font(r_sz, bold=r_bold)
                        
                        for ch in run.text:
                            if ch == "\n":
                                cur_x = start_x
                                cur_y += int(r_sz * pt_scale * 1.35)
                                continue
                            bbox = draw.textbbox((cur_x, cur_y), ch, font=fnt)
                            ch_w = bbox[2] - bbox[0]
                            if cur_x + ch_w > max_right and cur_x > l + 20:
                                cur_x = start_x
                                cur_y += int(r_sz * pt_scale * 1.35)
                            draw.text((cur_x, cur_y), ch, fill=r_col, font=fnt)
                            cur_x += ch_w
                else:
                    fnt = get_font(11, bold=False)
                    bbox = draw.textbbox((0, 0), p_text, font=fnt)
                    p_width = bbox[2] - bbox[0]
                    cur_y = t + 2 + p_idx * 20
                    if p.alignment == 2:
                        cur_x = l + max(0, (w - p_width) / 2)
                    elif p.alignment == 3:
                        cur_x = l + max(0, w - p_width - 8)
                    else:
                        cur_x = l + 4
                    draw.text((cur_x, cur_y), p_text, fill=(15, 23, 42, 255), font=fnt)

    os.makedirs(os.path.dirname(os.path.abspath(out_img_path)), exist_ok=True)
    img.convert("RGB").save(out_img_path)
    print(f"[Renderer] Faithfully rendered PPTX to: {out_img_path}")
    return out_img_path


def compare_and_generate_diff(
    orig_img_path: str,
    sim_img_path: str,
    diff_out_path: str,
    crop_box: Optional[List[float]] = None,
    block_title: Optional[str] = None,
) -> str:
    """Generate side-by-side diff for full slide or cropped sub-block with automatic canvas registration."""
    raw_orig = Image.open(orig_img_path).convert("RGB")
    sim = Image.open(sim_img_path).convert("RGB")

    cl, ct, cr, cb = detect_inner_slide_canvas(raw_orig)
    orig_canvas = raw_orig.crop((cl, ct, cr, cb))

    w, h = 1440, 810
    orig = orig_canvas.resize((w, h), Image.Resampling.LANCZOS)
    sim = sim.resize((w, h), Image.Resampling.LANCZOS)

    # Optional 0-1000 Box Cropping for Block-Level Comparison
    if crop_box and len(crop_box) == 4:
        l, t, bw, bh = crop_box
        px_l = max(0, int(l / 1000.0 * w))
        px_t = max(0, int(t / 1000.0 * h))
        px_r = min(w, int((l + bw) / 1000.0 * w))
        px_b = min(h, int((t + bh) / 1000.0 * h))
        orig = orig.crop((px_l, px_t, px_r, px_b))
        sim = sim.crop((px_l, px_t, px_r, px_b))
        w, h = orig.size

    header_h = 55
    canvas = Image.new("RGB", (w * 2 + 30, h + header_h), (15, 23, 42))
    canvas.paste(orig, (0, header_h))
    canvas.paste(sim, (w + 30, header_h))

    title_suffix = f" [{block_title}]" if block_title else ""

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([10, 8, 320, 46], fill=(30, 41, 59))
    draw.text((25, 18), f"ORIGINAL (Ground Truth){title_suffix}", fill=(56, 189, 248))

    draw.rectangle([w + 40, 8, w + 440, 46], fill=(30, 41, 59))
    draw.text((w + 55, 18), f"RESTORED 100% PURE VECTOR{title_suffix}", fill=(74, 222, 128))

    os.makedirs(os.path.dirname(os.path.abspath(diff_out_path)), exist_ok=True)
    canvas.save(diff_out_path)
    print(f"[Diff] Side-by-side comparison saved to: {diff_out_path}")
    return diff_out_path


def main():
    parser = argparse.ArgumentParser(description="Render PPTX and generate Visual Diff.")
    parser.add_argument("pptx", nargs="?", default="output/slide_02.pptx", help="Path to PPTX file")
    parser.add_argument("orig", nargs="?", default="input/slide_02.png", help="Path to original image")
    parser.add_argument("-o", "--output", default="output/diff_slide_02.png", help="Output diff path")
    parser.add_argument("--crop-box", nargs=4, type=float, default=None, metavar=("L", "T", "W", "H"), help="Optional 0-1000 crop box")
    parser.add_argument("--block-title", default=None, help="Optional block title")
    parser.add_argument("--cumulative-out", default=None, help="Optional path to save full cumulative preview render")
    parser.add_argument("--dual-preview", action="store_true", help="Generate both slice diff and cumulative full preview")

    args = parser.parse_args()
    sim_img = args.cumulative_out or "output/sim_preview.png"
    render_pptx_to_image(args.pptx, sim_img)
    compare_and_generate_diff(args.orig, sim_img, args.output, crop_box=args.crop_box, block_title=args.block_title)
    if args.cumulative_out:
        print(f"[Preview] Cumulative full preview saved to: {args.cumulative_out}")


if __name__ == "__main__":
    main()
