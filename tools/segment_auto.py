"""segment_auto.py — Fully Automatic Deterministic Macro Block Boundary Detector

Analyzes visual projection profiles, color variance gradients, and structural boundary splits
to automatically segment a presentation slide into discrete normalized blocks (0-1000 coordinate system).

Zero external dependencies (Pure PIL + Python math).
"""

import os
import sys
import math
import json
import argparse
from typing import List, Dict, Tuple, Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.render_and_diff import detect_inner_slide_canvas


def get_chinese_font(size: int = 18) -> ImageFont.ImageFont:
    """Load robust Chinese font with fallbacks."""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size, index=0)
            except Exception:
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
    return ImageFont.load_default()


DEFAULT_PALETTE = [
    (29, 78, 216),   # Royal Blue
    (5, 150, 105),   # Emerald Green
    (217, 119, 6),   # Amber/Orange
    (124, 58, 237),  # Purple
    (225, 29, 72),   # Rose Red
    (13, 148, 136),  # Teal
    (79, 70, 229),   # Indigo
]


def detect_slide_blocks(img_path: str, min_block_height_pct: float = 0.08) -> List[Dict[str, Any]]:
    """
    Detect major visual blocks on slide canvas using horizontal and vertical projection profiling.
    """
    raw_img = Image.open(img_path).convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    w, h = canvas.size

    # 1. Row variance profile to find major horizontal section cuts
    row_variances = []
    for y in range(0, h, 2):
        row_px = [canvas.getpixel((x, y)) for x in range(20, w - 20, 8)]
        mean_lum = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in row_px) / len(row_px)
        var = sum(((0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) - mean_lum) ** 2 for p in row_px) / len(row_px)
        row_variances.append(var)

    # 2. Identify horizontal band boundaries
    min_cut_dist_px = int(h * min_block_height_pct)
    h_cuts = [0]

    # Detect Header boundary (~Y=80..110)
    # Detect Summary Banner boundary (~Y=170..200)
    # Detect Mid KPI boundary (~Y=300..340)
    for y_idx in range(len(row_variances) - 1):
        actual_y = y_idx * 2
        # Look for local troughs in variance between content clusters
        if actual_y - h_cuts[-1] >= min_cut_dist_px:
            # Check if this row is near white background (separating space)
            row_px = [canvas.getpixel((x, actual_y)) for x in range(40, w - 40, 10)]
            avg_white = sum(1 for p in row_px if p[0] > 240 and p[1] > 240 and p[2] > 240) / len(row_px)
            if avg_white > 0.85 and actual_y < h - min_cut_dist_px:
                h_cuts.append(actual_y)

    h_cuts.append(h)

    # 3. Form blocks, checking for vertical 2-column split in bottom half
    blocks = []
    block_id = 1

    for i in range(len(h_cuts) - 1):
        top_y = h_cuts[i]
        bot_y = h_cuts[i + 1]
        bh_px = bot_y - top_y

        if bh_px < 30:
            continue

        # Check if this horizontal band contains a 2-column split
        mid_y = (top_y + bot_y) // 2
        col_variances = []
        for x in range(0, w, 4):
            col_px = [canvas.getpixel((x, y)) for y in range(top_y + 10, bot_y - 10, max(2, bh_px // 6))]
            if not col_px:
                col_variances.append(0)
                continue
            mean_c = sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in col_px) / len(col_px)
            var = sum(((0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) - mean_c) ** 2 for p in col_px) / len(col_px)
            col_variances.append(var)

        # Look for a central vertical gap (around x=w//2 ± 15%)
        split_x = None
        min_gap_var = float("inf")
        center_l = int(w * 0.42 / 4)
        center_r = int(w * 0.58 / 4)

        for c_idx in range(center_l, min(len(col_variances), center_r)):
            actual_x = c_idx * 4
            # Check vertical strip at actual_x
            strip_px = [canvas.getpixel((actual_x, y)) for y in range(top_y + 10, bot_y - 10, 8)]
            if strip_px:
                white_ratio = sum(1 for p in strip_px if p[0] > 240 and p[1] > 240 and p[2] > 240) / len(strip_px)
                if white_ratio > 0.85:
                    split_x = actual_x
                    break

        if split_x and bh_px > 180:
            # 2-column split (e.g. Left Table / Right Strategy Card)
            # Left block
            l1, t1, w1, h1 = 30, round(top_y / h * 1000), round((split_x - 40) / w * 1000), round(bh_px / h * 1000)
            blocks.append({
                "id": f"Block {block_id}",
                "name": f"Left Section {block_id}",
                "box": [l1, t1, w1, h1],
                "color": DEFAULT_PALETTE[(block_id - 1) % len(DEFAULT_PALETTE)],
            })
            block_id += 1

            # Right block
            l2, t2, w2, h2 = round((split_x + 10) / w * 1000), round(top_y / h * 1000), round((w - split_x - 40) / w * 1000), round(bh_px / h * 1000)
            blocks.append({
                "id": f"Block {block_id}",
                "name": f"Right Section {block_id}",
                "box": [l2, t2, w2, h2],
                "color": DEFAULT_PALETTE[(block_id - 1) % len(DEFAULT_PALETTE)],
            })
            block_id += 1
        else:
            # Single full-width horizontal block
            norm_l = 30
            norm_t = round(top_y / h * 1000)
            norm_w = 940
            norm_h = round(bh_px / h * 1000)
            blocks.append({
                "id": f"Block {block_id}",
                "name": f"Section {block_id}",
                "box": [norm_l, norm_t, norm_w, norm_h],
                "color": DEFAULT_PALETTE[(block_id - 1) % len(DEFAULT_PALETTE)],
            })
            block_id += 1

    return blocks


def render_block_map(img_path: str, blocks: List[Dict[str, Any]], out_map_path: str) -> str:
    """Render annotated visual block overlay map."""
    raw_img = Image.open(img_path).convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

    annotated = canvas.copy().convert("RGBA")
    overlay = Image.new("RGBA", (1440, 810), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fnt = get_chinese_font(18)
    w, h = 1440, 810

    for idx, b in enumerate(blocks):
        l, t, bw, bh = b["box"]
        px_l = int(l / 1000.0 * w)
        px_t = int(t / 1000.0 * h)
        px_r = int((l + bw) / 1000.0 * w)
        px_b = int((t + bh) / 1000.0 * h)

        c = b.get("color", DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)])
        fill_c = (c[0], c[1], c[2], 30)
        border_c = (c[0], c[1], c[2], 235)

        draw.rounded_rectangle([px_l, px_t, px_r, px_b], radius=8, fill=fill_c, outline=border_c, width=3)

        b_id = b.get("id", f"Block {idx+1}")
        b_name = b.get("name", "Section")
        lbl_text = f" {b_id}: {b_name} [Y={t}..{t+bh}] "
        bbox = draw.textbbox((0, 0), lbl_text, font=fnt)
        lbl_w = bbox[2] - bbox[0] + 16
        lbl_h = 28

        badge_top = max(4, px_t + 6)
        badge_left = px_l + 8

        draw.rounded_rectangle([badge_left, badge_top, badge_left + lbl_w, badge_top + lbl_h], radius=5, fill=(c[0], c[1], c[2], 245))
        draw.text((badge_left + 8, badge_top + 4), lbl_text, fill=(255, 255, 255, 255), font=fnt)

    annotated = Image.alpha_composite(annotated, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(out_map_path)), exist_ok=True)
    annotated.save(out_map_path)
    print(f"[AutoSegment] Visual block map saved to: {out_map_path}")
    return out_map_path


def main():
    parser = argparse.ArgumentParser(description="Fully Automated Deterministic Slide Block Segmentation.")
    parser.add_argument("image", nargs="?", default="input/slide_02.png", help="Input slide image path")
    parser.add_argument("-o", "--output", default=None, help="Output block map image path")
    parser.add_argument("--json", default=None, help="Save detected blocks as JSON file")
    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.image))[0]
    map_out = args.output or f"output/block_map_auto_{base_name}.png"
    json_out = args.json or f"output/blocks_auto_{base_name}.json"

    print(f"[AutoSegment] Analyzing visual layout structure: {args.image}")
    blocks = detect_slide_blocks(args.image)
    render_block_map(args.image, blocks, map_out)

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)
    print(f"[AutoSegment] Block specification saved to: {json_out}")

    print("\n" + "=" * 60)
    print("📊 Auto-Detected Macro Blocks (Normalized 0-1000):")
    print("=" * 60)
    for b in blocks:
        print(f"  • {b['id']:<10}: box={b['box']} ({b['name']})")
    print("=" * 60)


if __name__ == "__main__":
    main()
