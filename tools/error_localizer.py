"""error_localizer.py — 结构化像素误差定位器

对比「原图」和「PPTX 渲染图」，针对 block_spec 中定义的每个已知元素，
自动输出结构化修复指令，无需多模态 LLM 看图判断。

输出格式：
[
  {
    "element": "顶部横幅 bg_color",
    "box_norm": [480, 318, 494, 82],
    "error_type": "color_mismatch",
    "severity": "high",       # high / medium / low
    "orig_value": "#2167BA",
    "pptx_value": "#2A6EC5",
    "delta_e": 18.3,
    "fix_suggestion": 'bg_color="#2167BA"'
  },
  ...
]

Zero external dependencies (Pure PIL + Python math only).
"""

import os
import sys
import math
import json
import argparse
from typing import List, Tuple, Dict, Optional, Any

from PIL import Image, ImageStat, ImageFilter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.render_and_diff import render_pptx_to_image, detect_inner_slide_canvas


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def color_distance(c1: Tuple, c2: Tuple) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))


def norm_box_to_px(box_norm: List[float], w: int, h: int) -> Tuple[int, int, int, int]:
    l, t, bw, bh = box_norm
    px_l = max(0, int(l / 1000.0 * w))
    px_t = max(0, int(t / 1000.0 * h))
    px_r = min(w, int((l + bw) / 1000.0 * w))
    px_b = min(h, int((t + bh) / 1000.0 * h))
    return px_l, px_t, px_r, px_b


def sample_region_avg(img: Image.Image, px_l: int, px_t: int,
                      px_r: int, px_b: int, margin: int = 3) -> Tuple[int, int, int]:
    """Average color of the interior of a region (excluding edge pixels)."""
    px_l = min(px_l + margin, px_r - 1)
    px_t = min(px_t + margin, px_b - 1)
    px_r = max(px_r - margin, px_l + 1)
    px_b = max(px_b - margin, px_t + 1)
    crop = img.crop((px_l, px_t, px_r, px_b))
    stat = ImageStat.Stat(crop)
    r, g, b = [int(v) for v in stat.mean[:3]]
    return r, g, b


def sample_gradient_stops(img: Image.Image, px_l: int, px_t: int,
                           px_r: int, px_b: int, direction: str = "horizontal") -> List[Dict]:
    """Sample gradient start/end colors."""
    w = px_r - px_l
    h = px_b - px_t
    margin = max(2, min(w, h) // 10)

    if direction == "horizontal":
        left_r, left_g, left_b = sample_region_avg(img, px_l, px_t, px_l + margin * 3, px_b)
        right_r, right_g, right_b = sample_region_avg(img, px_r - margin * 3, px_t, px_r, px_b)
        return [
            {"pos": 0.0, "color": rgb_to_hex(left_r, left_g, left_b)},
            {"pos": 1.0, "color": rgb_to_hex(right_r, right_g, right_b)},
        ]
    else:  # vertical
        top_r, top_g, top_b = sample_region_avg(img, px_l, px_t, px_r, px_t + margin * 3)
        bot_r, bot_g, bot_b = sample_region_avg(img, px_l, px_b - margin * 3, px_r, px_b)
        return [
            {"pos": 0.0, "color": rgb_to_hex(top_r, top_g, top_b)},
            {"pos": 1.0, "color": rgb_to_hex(bot_r, bot_g, bot_b)},
        ]


def estimate_text_height_px(img: Image.Image, px_l: int, px_t: int,
                              px_r: int, px_b: int) -> Optional[int]:
    """Estimate the dominant text height in pixels using horizontal edge scan."""
    region = img.crop((px_l, px_t, px_r, px_b)).convert("L")
    edges = region.filter(ImageFilter.FIND_EDGES)
    w, h = edges.size
    if h == 0:
        return None

    # Find rows with significant edge activity
    active_rows = []
    pixels = edges.load()
    for y in range(h):
        row_sum = sum(pixels[x, y] for x in range(w))
        if row_sum > w * 15:  # threshold: average brightness > 15
            active_rows.append(y)

    if len(active_rows) < 2:
        return None

    # Estimate text block height as span of active rows
    return active_rows[-1] - active_rows[0] + 1


def px_height_to_pt(height_px: int, canvas_h_px: int = 810) -> float:
    """Convert pixel height on the canvas to PowerPoint font size (pt)."""
    # 1pt = canvas_h / 1000 * (72/96) normalized units
    # font_pt ≈ height_px / canvas_h * 1000 * (72/96) * scale
    # For PPTX: slide height = 7.5 inches = 540pt → 810px ↔ 540pt
    pt_per_px = 540.0 / canvas_h_px
    return round(height_px * pt_per_px, 1)


# ---------------------------------------------------------------------------
# Severity Grading
# ---------------------------------------------------------------------------

def grade_severity(delta_e: float) -> str:
    if delta_e > 40:
        return "critical"
    elif delta_e > 20:
        return "high"
    elif delta_e > 10:
        return "medium"
    else:
        return "low"


def grade_size_severity(pt_diff: float) -> str:
    if abs(pt_diff) > 6:
        return "critical"
    elif abs(pt_diff) > 3:
        return "high"
    elif abs(pt_diff) > 1:
        return "medium"
    else:
        return "low"


# ---------------------------------------------------------------------------
# Element-level Diff Checks
# ---------------------------------------------------------------------------

def check_bg_color(element_name: str, box_norm: List[float],
                   orig: Image.Image, pptx: Image.Image,
                   expected_type: str = "bg_color") -> Optional[Dict]:
    """Check if background color matches between orig and pptx render."""
    W, H = orig.size
    px_l, px_t, px_r, px_b = norm_box_to_px(box_norm, W, H)

    orig_color = sample_region_avg(orig, px_l, px_t, px_r, px_b)
    pptx_color = sample_region_avg(pptx, px_l, px_t, px_r, px_b)
    delta = color_distance(orig_color, pptx_color)

    if delta < 8:  # Within acceptable tolerance
        return None

    orig_hex = rgb_to_hex(*orig_color)
    pptx_hex = rgb_to_hex(*pptx_color)

    return {
        "element": element_name,
        "box_norm": box_norm,
        "error_type": "color_mismatch",
        "severity": grade_severity(delta),
        "orig_value": orig_hex,
        "pptx_value": pptx_hex,
        "delta_e": round(delta, 1),
        "fix_suggestion": f'{expected_type}="{orig_hex}"',
    }


def check_gradient(element_name: str, box_norm: List[float],
                   orig: Image.Image, pptx: Image.Image,
                   direction: str = "horizontal") -> List[Dict]:
    """Check if gradient colors match between orig and pptx render."""
    W, H = orig.size
    px_l, px_t, px_r, px_b = norm_box_to_px(box_norm, W, H)

    orig_stops = sample_gradient_stops(orig, px_l, px_t, px_r, px_b, direction)
    pptx_stops = sample_gradient_stops(pptx, px_l, px_t, px_r, px_b, direction)

    errors = []
    for i, (os_, ps_) in enumerate(zip(orig_stops, pptx_stops)):
        orig_rgb = tuple(int(os_["color"].lstrip("#")[j*2:j*2+2], 16) for j in range(3))
        pptx_rgb = tuple(int(ps_["color"].lstrip("#")[j*2:j*2+2], 16) for j in range(3))
        delta = color_distance(orig_rgb, pptx_rgb)
        pos_label = "start" if i == 0 else "end"

        if delta >= 8:
            errors.append({
                "element": f"{element_name} gradient_{pos_label}",
                "box_norm": box_norm,
                "error_type": "gradient_color_mismatch",
                "severity": grade_severity(delta),
                "orig_value": os_["color"],
                "pptx_value": ps_["color"],
                "delta_e": round(delta, 1),
                "fix_suggestion": f'gradient_colors=["{orig_stops[0]["color"]}", "{orig_stops[-1]["color"]}"]',
            })

    return errors


def check_position(element_name: str, box_norm_orig: List[float],
                   box_norm_pptx: List[float]) -> List[Dict]:
    """Check if element positions/sizes match."""
    errors = []
    labels = ["left", "top", "width", "height"]
    fix_keys = ["left", "top", "width", "height"]

    for i, (o, p, lbl) in enumerate(zip(box_norm_orig, box_norm_pptx, labels)):
        diff = abs(o - p)
        if diff > 5:  # 5 normalized units tolerance (~4px on 810h canvas)
            errors.append({
                "element": f"{element_name} {lbl}",
                "box_norm": box_norm_orig,
                "error_type": "position_mismatch",
                "severity": "high" if diff > 20 else "medium",
                "orig_value": f"{o:.0f}",
                "pptx_value": f"{p:.0f}",
                "delta_norm": round(diff, 1),
                "fix_suggestion": f"box[{i}] = {o:.0f}  (was {p:.0f}, diff={diff:.0f})",
            })

    return errors


def check_ssim_region(element_name: str, box_norm: List[float],
                      orig: Image.Image, pptx: Image.Image) -> Dict:
    """Compute pixel-level similarity score for a region."""
    W, H = orig.size
    px_l, px_t, px_r, px_b = norm_box_to_px(box_norm, W, H)

    orig_crop = orig.crop((px_l, px_t, px_r, px_b))
    pptx_crop = pptx.crop((px_l, px_t, px_r, px_b))

    # Resize pptx to match orig if different
    if orig_crop.size != pptx_crop.size:
        pptx_crop = pptx_crop.resize(orig_crop.size, Image.LANCZOS)

    w, h = orig_crop.size
    if w == 0 or h == 0:
        return {"element": element_name, "ssim": 1.0, "mean_delta_e": 0.0}

    orig_px = orig_crop.load()
    pptx_px = pptx_crop.load()

    total_delta = 0.0
    count = 0
    for y in range(h):
        for x in range(w):
            c1 = orig_px[x, y][:3]
            c2 = pptx_px[x, y][:3]
            total_delta += color_distance(c1, c2)
            count += 1

    mean_delta = total_delta / max(1, count)
    similarity = max(0.0, 1.0 - mean_delta / 150.0)

    return {
        "element": element_name,
        "box_norm": box_norm,
        "similarity_pct": round(similarity * 100, 1),
        "mean_delta_e": round(mean_delta, 1),
        "severity": grade_severity(mean_delta),
    }


# ---------------------------------------------------------------------------
# Main Localizer
# ---------------------------------------------------------------------------

def localize_errors(
    pptx_path: str,
    orig_img_path: str,
    block_spec: List[Dict],
    sim_img_path: str = "output/sim_preview.png",
) -> Dict[str, Any]:
    """
    Main entry: compare orig image vs PPTX render for each element in block_spec.

    block_spec format:
    [
      {
        "name": "顶部横幅",
        "box_norm": [480, 318, 494, 82],
        "type": "gradient_card",    # gradient_card | solid_card | badge | text | divider
        "gradient_direction": "horizontal",  # optional
        "expected_bg": "#FFFFFF",   # optional hint
      },
      ...
    ]
    """
    # Render PPTX to image
    print(f"[ErrorLocalizer] Rendering PPTX: {pptx_path}")
    render_pptx_to_image(pptx_path, sim_img_path)

    # Load and normalize both images to 1440x810
    raw_orig = Image.open(orig_img_path).convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_orig)
    orig = raw_orig.crop((cl, ct, cr, cb)).resize((1440, 810), Image.LANCZOS)
    pptx = Image.open(sim_img_path).convert("RGB").resize((1440, 810), Image.LANCZOS)

    all_errors = []
    region_summaries = []

    for elem in block_spec:
        name = elem.get("name", "unknown")
        box = elem.get("box_norm", elem.get("box", [0, 0, 1000, 1000]))
        elem_type = elem.get("type", "solid_card")

        # 1. Region similarity score
        region_sim = check_ssim_region(name, box, orig, pptx)
        region_summaries.append(region_sim)

        # 2. Background / solid color check
        if elem_type in ("solid_card", "badge", "divider"):
            err = check_bg_color(f"{name} bg_color", box, orig, pptx, "bg_color")
            if err:
                all_errors.append(err)

        # 3. Gradient check
        if elem_type == "gradient_card":
            grad_dir = elem.get("gradient_direction", "horizontal")
            grad_errors = check_gradient(f"{name} gradient", box, orig, pptx, grad_dir)
            all_errors.extend(grad_errors)

        # 4. Text region check (overall color tone)
        if elem_type == "text":
            err = check_bg_color(f"{name} text_region", box, orig, pptx, "font_color")
            if err:
                all_errors.append(err)

    # Sort errors by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_errors.sort(key=lambda e: sev_order.get(e.get("severity", "low"), 4))

    return {
        "total_errors": len(all_errors),
        "errors": all_errors,
        "region_summaries": region_summaries,
        "overall_similarity_pct": round(
            sum(r["similarity_pct"] for r in region_summaries) / max(1, len(region_summaries)), 1
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Structural Error Localizer — no multimodal LLM needed")
    parser.add_argument("pptx", help="Path to PPTX file")
    parser.add_argument("orig", help="Path to original slide PNG")
    parser.add_argument("--spec", required=True, help="Path to block_spec JSON file")
    parser.add_argument("--sim", default="output/sim_preview.png", help="Rendered PPTX image path")
    parser.add_argument("-o", "--output", default=None, help="Save error report JSON to file")
    args = parser.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        block_spec = json.load(f)

    report = localize_errors(args.pptx, args.orig, block_spec, sim_img_path=args.sim)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)
    print("\n" + "=" * 60)
    print("🔍 Structural Error Localization Report")
    print("=" * 60)
    print(f"Overall Similarity: {report['overall_similarity_pct']}%")
    print(f"Total Errors Found: {report['total_errors']}")
    print()

    if report["errors"]:
        print("📋 Fix Instructions (sorted by severity):")
        for i, err in enumerate(report["errors"], 1):
            print(f"\n  [{i}] {err['element']} — {err['severity'].upper()}")
            print(f"       Type: {err['error_type']}")
            print(f"       Original : {err.get('orig_value', 'N/A')}")
            print(f"       PPTX     : {err.get('pptx_value', 'N/A')}")
            if "delta_e" in err:
                print(f"       ΔE       : {err['delta_e']}")
            print(f"       Fix      : {err.get('fix_suggestion', 'N/A')}")
    else:
        print("✅ No significant errors found!")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n[ErrorLocalizer] Full report saved to: {args.output}")


if __name__ == "__main__":
    main()
