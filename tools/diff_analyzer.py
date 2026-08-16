"""Deterministic Quantitative Diff & Visual Heatmap Analyzer (tools/diff_analyzer.py)

Zero third-party dependencies (Pure PIL + Python math).

Calculates:
1. SSIM (Structural Similarity Index Measure) approximation via local windows
2. MSE (Mean Squared Error) & PSNR (Peak Signal-to-Noise Ratio)
3. Color Difference (Mean RGB Euclidean Distance & Error Pixel Rate)
4. 3-Way Visual Comparison Canvas: [ Ground Truth | Restored Vector PPTX | Thermal Pixel Error Heatmap ]
"""

import os
import sys
import math
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.render_and_diff import detect_inner_slide_canvas, render_pptx_to_image


def get_chinese_font(size: int = 16) -> ImageFont.ImageFont:
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


def calculate_metrics_and_heatmap(
    img1: Image.Image,
    img2: Image.Image,
    max_delta: float = 100.0,
) -> Tuple[Dict[str, Any], Image.Image]:
    """Calculate MSE, PSNR, SSIM approximation, and generate thermal heatmap image."""
    w, h = img1.size
    p1 = img1.load()
    p2 = img2.load()

    total_sq_err = 0.0
    total_diff = 0.0
    visible_err_pixels = 0
    total_pixels = w * h

    # Gray luminance values for SSIM
    lum1_sum = 0.0
    lum2_sum = 0.0

    # Prepare heatmap output
    heatmap = Image.new("RGB", (w, h), (15, 23, 42))
    hp = heatmap.load()

    # Track row-level and column-level error profiles
    row_errors = [0.0] * h
    col_errors = [0.0] * w

    for y in range(h):
        for x in range(w):
            r1, g1, b1 = p1[x, y][:3]
            r2, g2, b2 = p2[x, y][:3]

            dr = r1 - r2
            dg = g1 - g2
            db = b1 - b2

            # Euclidean color distance
            dist = math.sqrt(dr * dr + dg * dg + db * db)
            sq_err = (dr * dr + dg * dg + db * db) / 3.0

            total_sq_err += sq_err
            total_diff += dist
            row_errors[y] += dist
            col_errors[x] += dist

            if dist > 25.0:  # Noticeable perceptual difference threshold
                visible_err_pixels += 1

            # Luminance
            y1 = 0.299 * r1 + 0.587 * g1 + 0.114 * b1
            y2 = 0.299 * r2 + 0.587 * g2 + 0.114 * b2
            lum1_sum += y1
            lum2_sum += y2

            # Thermal Jet-style Colormap
            norm = min(1.0, max(0.0, dist / max_delta))
            if norm < 0.06:
                # Neutral dark blue background for zero/tiny error
                hr, hg, hb = 15, 23, 42
            else:
                # 4-stage color ramp: Blue -> Cyan -> Yellow -> Bright Red
                if norm < 0.25:
                    t = norm / 0.25
                    hr, hg, hb = 0, int(200 * t), 255
                elif norm < 0.5:
                    t = (norm - 0.25) / 0.25
                    hr, hg, hb = 0, 255, int(255 * (1 - t))
                elif norm < 0.75:
                    t = (norm - 0.5) / 0.25
                    hr, hg, hb = int(255 * t), 255, 0
                else:
                    t = (norm - 0.75) / 0.25
                    hr, hg, hb = 255, int(255 * (1 - t)), 0

            hp[x, y] = (hr, hg, hb)

    mse = total_sq_err / total_pixels
    psnr = 10 * math.log10((255.0 ** 2) / (mse + 1e-9)) if mse > 0 else 99.99
    mean_color_delta = total_diff / total_pixels
    err_pct = (visible_err_pixels / total_pixels) * 100.0

    # SSIM calculation
    mu1 = lum1_sum / total_pixels
    mu2 = lum2_sum / total_pixels

    var1_sum = 0.0
    var2_sum = 0.0
    cov_sum = 0.0

    # Sample-based variance & covariance for speed
    step = 2
    sample_count = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r1, g1, b1 = p1[x, y][:3]
            r2, g2, b2 = p2[x, y][:3]
            y1 = 0.299 * r1 + 0.587 * g1 + 0.114 * b1
            y2 = 0.299 * r2 + 0.587 * g2 + 0.114 * b2

            var1_sum += (y1 - mu1) ** 2
            var2_sum += (y2 - mu2) ** 2
            cov_sum += (y1 - mu1) * (y2 - mu2)
            sample_count += 1

    sigma1_sq = var1_sum / max(1, sample_count)
    sigma2_sq = var2_sum / max(1, sample_count)
    sigma12 = cov_sum / max(1, sample_count)

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / ((mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2))
    ssim = max(0.0, min(1.0, ssim))

    # Top Error Rows & Columns
    max_err_y = max(range(h), key=lambda y: row_errors[y])
    max_err_x = max(range(w), key=lambda x: col_errors[x])

    metrics = {
        "ssim": round(ssim, 4),
        "similarity_pct": round(ssim * 100.0, 2),
        "psnr_db": round(psnr, 2),
        "mse": round(mse, 2),
        "mean_color_delta": round(mean_color_delta, 2),
        "visible_error_pixel_pct": round(err_pct, 2),
        "max_error_coord_px": {"x": max_err_x, "y": max_err_y},
    }

    return metrics, heatmap


def analyze_and_build_triptych(
    orig_img_path: str,
    sim_img_path: str,
    out_diff_path: str,
    crop_box: Optional[List[float]] = None,
    block_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Run deterministic quantitative diff analysis, build 3-way canvas, and save."""
    raw_orig = Image.open(orig_img_path).convert("RGB")
    sim_full = Image.open(sim_img_path).convert("RGB")

    cl, ct, cr, cb = detect_inner_slide_canvas(raw_orig)
    orig_canvas = raw_orig.crop((cl, ct, cr, cb))

    w_canvas, h_canvas = 1440, 810
    orig = orig_canvas.resize((w_canvas, h_canvas), Image.Resampling.LANCZOS)
    sim = sim_full.resize((w_canvas, h_canvas), Image.Resampling.LANCZOS)

    # Optional 0-1000 Box Crop
    if crop_box and len(crop_box) == 4:
        l, t, bw, bh = crop_box
        px_l = max(0, int(l / 1000.0 * w_canvas))
        px_t = max(0, int(t / 1000.0 * h_canvas))
        px_r = min(w_canvas, int((l + bw) / 1000.0 * w_canvas))
        px_b = min(h_canvas, int((t + bh) / 1000.0 * h_canvas))
        orig = orig.crop((px_l, px_t, px_r, px_b))
        sim = sim.crop((px_l, px_t, px_r, px_b))

    w, h = orig.size

    # Calculate metrics & heatmap
    metrics, heatmap = calculate_metrics_and_heatmap(orig, sim)
    metrics["block"] = block_title or "Full Slide"
    metrics["crop_box_0_1000"] = crop_box

    # Build 3-Way Canvas
    header_h = 55
    canvas_w = w * 3 + 40
    canvas_h = h + header_h
    triptych = Image.new("RGB", (canvas_w, canvas_h), (15, 23, 42))

    triptych.paste(orig, (0, header_h))
    triptych.paste(sim, (w + 20, header_h))
    triptych.paste(heatmap, (w * 2 + 40, header_h))

    draw = ImageDraw.Draw(triptych)
    fnt = get_chinese_font(15)

    # Panel 1: Ground Truth
    draw.rectangle([8, 8, w - 8, 46], fill=(30, 41, 59))
    draw.text((16, 16), f"1. ORIGINAL [Ground Truth] {block_title or ''}", fill=(56, 189, 248), font=fnt)

    # Panel 2: Restored PPTX
    draw.rectangle([w + 25, 8, w * 2 + 10, 46], fill=(30, 41, 59))
    draw.text((w + 35, 16), f"2. RESTORED PPTX (SSIM: {metrics['similarity_pct']}%)", fill=(74, 222, 128), font=fnt)

    # Panel 3: Error Heatmap
    draw.rectangle([w * 2 + 45, 8, canvas_w - 8, 46], fill=(30, 41, 59))
    draw.text((w * 2 + 55, 16), f"3. PIXEL HEATMAP (Avg Δ: {metrics['mean_color_delta']})", fill=(244, 63, 94), font=fnt)

    os.makedirs(os.path.dirname(os.path.abspath(out_diff_path)), exist_ok=True)
    triptych.save(out_diff_path)
    print(f"[DiffAnalyzer] Saved 3-way analysis to: {out_diff_path}")

    metrics["triptych_path"] = out_diff_path
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Deterministic Visual Diff & Heatmap Analyzer.")
    parser.add_argument("pptx", nargs="?", default="output/slide_02.pptx", help="Path to PPTX")
    parser.add_argument("orig", nargs="?", default="input/slide_02.png", help="Path to original image")
    parser.add_argument("-o", "--output", default="output/diff_triptych_block_04.png", help="Output triptych path")
    parser.add_argument("--crop-box", nargs=4, type=float, default=None, metavar=("L", "T", "W", "H"), help="0-1000 crop box")
    parser.add_argument("--block-title", default=None, help="Block title")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON only")

    args = parser.parse_args()
    sim_tmp = "output/sim_preview.png"
    render_pptx_to_image(args.pptx, sim_tmp)
    metrics = analyze_and_build_triptych(args.orig, sim_tmp, args.output, crop_box=args.crop_box, block_title=args.block_title)
    
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False))
    else:
        print("\n" + "=" * 60)
        print("📊 Deterministic Quantitative Analysis Report:")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        print("=" * 60)


if __name__ == "__main__":
    main()
