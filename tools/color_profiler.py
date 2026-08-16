"""color_profiler.py — 全自动颜色/渐变/边框提取器

给定原图 + 0-1000 归一化 block box，自动输出：
- dominant_colors: 区域主色（K-means 聚类 top-5）
- gradient_direction: 'horizontal' | 'vertical' | 'diagonal' | 'solid'
- gradient_stops: [(position, hex_color)]
- border_color: 边框颜色
- bg_color: 主背景色

Zero external dependencies (Pure PIL + Python math only).
"""

import os
import sys
import math
import json
import argparse
from typing import List, Tuple, Dict, Optional, Any

from PIL import Image, ImageStat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ---------------------------------------------------------------------------
# Core Utilities
# ---------------------------------------------------------------------------

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def color_distance(c1: Tuple, c2: Tuple) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))


def norm_box_to_px(box_norm: List[float], w: int, h: int) -> Tuple[int, int, int, int]:
    """Convert 0-1000 normalized [l, t, bw, bh] to pixel [l, t, r, b]."""
    l, t, bw, bh = box_norm
    px_l = max(0, int(l / 1000.0 * w))
    px_t = max(0, int(t / 1000.0 * h))
    px_r = min(w, int((l + bw) / 1000.0 * w))
    px_b = min(h, int((t + bh) / 1000.0 * h))
    return px_l, px_t, px_r, px_b


def sample_pixel(img: Image.Image, x: int, y: int) -> Tuple[int, int, int]:
    return img.getpixel((x, y))[:3]


# ---------------------------------------------------------------------------
# K-means color clustering (pure Python, no sklearn)
# ---------------------------------------------------------------------------

def kmeans_colors(pixels: List[Tuple], k: int = 5, iterations: int = 12) -> List[Tuple]:
    """Simple K-means clustering to find dominant colors."""
    if not pixels:
        return []
    k = min(k, len(pixels))
    # Initialize centroids by sampling evenly
    step = max(1, len(pixels) // k)
    centroids = [pixels[i * step] for i in range(k)]

    for _ in range(iterations):
        clusters: List[List[Tuple]] = [[] for _ in range(k)]
        for px in pixels:
            dists = [color_distance(px, c) for c in centroids]
            clusters[dists.index(min(dists))].append(px)

        new_centroids = []
        for i, cluster in enumerate(clusters):
            if cluster:
                r = int(sum(p[0] for p in cluster) / len(cluster))
                g = int(sum(p[1] for p in cluster) / len(cluster))
                b = int(sum(p[2] for p in cluster) / len(cluster))
                new_centroids.append((r, g, b))
            else:
                new_centroids.append(centroids[i])
        centroids = new_centroids

    # Sort by cluster size (descending)
    cluster_sizes = []
    for c in centroids:
        size = sum(1 for px in pixels if color_distance(px, c) == min(color_distance(px, cc) for cc in centroids))
        cluster_sizes.append((size, c))
    cluster_sizes.sort(reverse=True)
    return [c for _, c in cluster_sizes]


# ---------------------------------------------------------------------------
# Gradient Detection
# ---------------------------------------------------------------------------

def detect_gradient(img: Image.Image, px_l: int, px_t: int, px_r: int, px_b: int,
                    samples: int = 8) -> Dict[str, Any]:
    """Detect if region has a gradient and its direction."""
    w = px_r - px_l
    h = px_b - px_t
    if w < 4 or h < 4:
        return {"direction": "solid", "stops": []}

    # Sample left / center / right columns (midpoint row)
    mid_y = px_t + h // 2
    left_x  = px_l + max(1, w // 10)
    right_x = px_r - max(1, w // 10)
    top_y   = px_t + max(1, h // 10)
    bot_y   = px_b - max(1, h // 10)

    left_col  = sample_pixel(img, left_x, mid_y)
    right_col = sample_pixel(img, right_x, mid_y)
    top_row   = sample_pixel(img, px_l + w // 2, top_y)
    bot_row   = sample_pixel(img, px_l + w // 2, bot_y)

    horiz_delta = color_distance(left_col, right_col)
    vert_delta  = color_distance(top_row, bot_row)

    # Collect column-averaged samples for gradient stops
    def avg_col_at(x_pct: float) -> Tuple[int, int, int]:
        x = px_l + int(x_pct * w)
        x = max(px_l, min(px_r - 1, x))
        sampled = [sample_pixel(img, x, py) for py in range(px_t, px_b, max(1, h // 10))]
        r = int(sum(p[0] for p in sampled) / len(sampled))
        g = int(sum(p[1] for p in sampled) / len(sampled))
        b = int(sum(p[2] for p in sampled) / len(sampled))
        return r, g, b

    def avg_row_at(y_pct: float) -> Tuple[int, int, int]:
        y = px_t + int(y_pct * h)
        y = max(px_t, min(px_b - 1, y))
        sampled = [sample_pixel(img, px, y) for px in range(px_l, px_r, max(1, w // 10))]
        r = int(sum(p[0] for p in sampled) / len(sampled))
        g = int(sum(p[1] for p in sampled) / len(sampled))
        b = int(sum(p[2] for p in sampled) / len(sampled))
        return r, g, b

    GRADIENT_THRESHOLD = 18.0  # ΔE threshold to declare a gradient

    if horiz_delta > GRADIENT_THRESHOLD and horiz_delta >= vert_delta:
        # Horizontal gradient — sample 5 stops
        stops = []
        for i, pct in enumerate([0.02, 0.25, 0.50, 0.75, 0.98]):
            c = avg_col_at(pct)
            stops.append({"pos": round(pct, 2), "color": rgb_to_hex(*c)})
        return {"direction": "horizontal", "stops": stops,
                "start_color": rgb_to_hex(*avg_col_at(0.02)),
                "end_color": rgb_to_hex(*avg_col_at(0.98)),
                "delta_e": round(horiz_delta, 1)}

    elif vert_delta > GRADIENT_THRESHOLD:
        # Vertical gradient
        stops = []
        for pct in [0.02, 0.25, 0.50, 0.75, 0.98]:
            c = avg_row_at(pct)
            stops.append({"pos": round(pct, 2), "color": rgb_to_hex(*c)})
        return {"direction": "vertical", "stops": stops,
                "start_color": rgb_to_hex(*avg_row_at(0.02)),
                "end_color": rgb_to_hex(*avg_row_at(0.98)),
                "delta_e": round(vert_delta, 1)}

    else:
        # Solid color — return center average
        center_color = avg_col_at(0.5)
        return {"direction": "solid",
                "color": rgb_to_hex(*center_color),
                "stops": [{"pos": 0.5, "color": rgb_to_hex(*center_color)}]}


# ---------------------------------------------------------------------------
# Border Detection
# ---------------------------------------------------------------------------

def detect_border(img: Image.Image, px_l: int, px_t: int, px_r: int, px_b: int,
                  probe_depth: int = 3) -> Dict[str, Any]:
    """Sample border pixels to detect border color and width."""
    # Sample edge pixels (top, right, bottom, left)
    top_samples = [sample_pixel(img, x, px_t + 1) for x in range(px_l + 2, px_r - 2, max(1, (px_r - px_l) // 8))]
    right_samples = [sample_pixel(img, px_r - 2, y) for y in range(px_t + 2, px_b - 2, max(1, (px_b - px_t) // 8))]

    all_edge = top_samples + right_samples
    if not all_edge:
        return {"color": "transparent", "width_pt": 0}

    # Average edge color
    r = int(sum(p[0] for p in all_edge) / len(all_edge))
    g = int(sum(p[1] for p in all_edge) / len(all_edge))
    b = int(sum(p[2] for p in all_edge) / len(all_edge))

    # Compare to interior color — if very different, likely a real border
    interior_color = sample_pixel(img, (px_l + px_r) // 2, (px_t + px_b) // 2)
    edge_color = (r, g, b)
    delta = color_distance(edge_color, interior_color)

    if delta < 12:
        return {"color": "transparent", "width_pt": 0}
    else:
        return {"color": rgb_to_hex(*edge_color), "width_pt": round(delta / 30, 1)}


# ---------------------------------------------------------------------------
# Y-Axis Background Color Change-Point & Sub-Container Detector
# ---------------------------------------------------------------------------

def detect_vertical_strips(img: Image.Image, px_l: int, px_t: int, px_r: int, px_b: int,
                           w_canvas: int, h_canvas: int) -> List[Dict[str, Any]]:
    """
    Detects vertical background color change-points to distinguish between:
    - title_strip: narrow colored banner (height 15-55px) followed by white space
    - full_card: contiguous colored box covering entire section (> 90px)
    - plain_text_area: white/canvas background area where body text sits directly
    """
    w = px_r - px_l
    h = px_b - px_t
    if h < 20:
        return []

    # 1. Sample background color for each horizontal row (sampling middle 60% of width to avoid text edge shadows)
    row_colors = []
    x_samples = [px_l + int(w * f) for f in [0.25, 0.40, 0.60, 0.75]]

    for y in range(px_t, px_b):
        pxs = [sample_pixel(img, x, y) for x in x_samples]
        # Robust row background: take brightest/most dominant non-black pixel
        sorted_px = sorted(pxs, key=lambda p: p[0] + p[1] + p[2], reverse=True)
        r, g, b = sorted_px[0]
        # Is this row white/canvas background?
        is_white = (r > 246 and g > 246 and b > 246)
        row_colors.append((y, (r, g, b), is_white))

    # 2. Group into contiguous segments of [colored] vs [white]
    segments = []
    curr_type = "white" if row_colors[0][2] else "colored"
    start_y = row_colors[0][0]
    segment_rgbs = [row_colors[0][1]]

    for y, rgb, is_white in row_colors[1:]:
        t = "white" if is_white else "colored"
        if t == curr_type:
            segment_rgbs.append(rgb)
        else:
            avg_r = int(sum(c[0] for c in segment_rgbs) / len(segment_rgbs))
            avg_g = int(sum(c[1] for c in segment_rgbs) / len(segment_rgbs))
            avg_b = int(sum(c[2] for c in segment_rgbs) / len(segment_rgbs))
            segments.append({
                "type": curr_type,
                "start_y": start_y,
                "end_y": y,
                "height_px": y - start_y,
                "avg_color": rgb_to_hex(avg_r, avg_g, avg_b),
            })
            curr_type = t
            start_y = y
            segment_rgbs = [rgb]

    # Add final segment
    if segment_rgbs:
        avg_r = int(sum(c[0] for c in segment_rgbs) / len(segment_rgbs))
        avg_g = int(sum(c[1] for c in segment_rgbs) / len(segment_rgbs))
        avg_b = int(sum(c[2] for c in segment_rgbs) / len(segment_rgbs))
        segments.append({
            "type": curr_type,
            "start_y": start_y,
            "end_y": px_b,
            "height_px": px_b - start_y,
            "avg_color": rgb_to_hex(avg_r, avg_g, avg_b),
        })

    # 3. Classify each segment into structured sub_containers
    sub_containers = []
    for seg in segments:
        norm_l = round(px_l / w_canvas * 1000)
        norm_t = round(seg["start_y"] / h_canvas * 1000)
        norm_w = round(w / w_canvas * 1000)
        norm_h = round(seg["height_px"] / h_canvas * 1000)
        box_norm = [norm_l, norm_t, norm_w, norm_h]

        if seg["type"] == "colored":
            if seg["height_px"] <= 55:  # Narrow strip -> title_strip
                sub_containers.append({
                    "type": "title_strip",
                    "box_norm": box_norm,
                    "height_px": seg["height_px"],
                    "bg_color": seg["avg_color"],
                    "note": "Localized title bar background (bullets below sit on pure white)",
                })
            else:  # Wide box -> full_card
                sub_containers.append({
                    "type": "full_card",
                    "box_norm": box_norm,
                    "height_px": seg["height_px"],
                    "bg_color": seg["avg_color"],
                    "note": "Contiguous container card covering full content",
                })
        else:
            if seg["height_px"] > 15:
                sub_containers.append({
                    "type": "plain_text_area",
                    "box_norm": box_norm,
                    "height_px": seg["height_px"],
                    "bg_color": "#FFFFFF",
                    "note": "Direct canvas/white background for body bullets",
                })

    return sub_containers


# ---------------------------------------------------------------------------
# Main Profile Function
# ---------------------------------------------------------------------------

def profile_block(img_path: str, box_norm: List[float],
                  sample_step: int = 4,
                  top_k_colors: int = 5) -> Dict[str, Any]:
    """
    Fully automatic color profiler for a single block region.

    Args:
        img_path: Path to original slide PNG
        box_norm: [left, top, width, height] in 0-1000 normalized coords
        sample_step: Pixel sampling step (smaller = more accurate, slower)
        top_k_colors: Number of dominant colors to extract

    Returns:
        dict with keys: gradient, border, dominant_colors, bg_color, sub_containers
    """
    img = Image.open(img_path).convert("RGB")
    W, H = img.size
    px_l, px_t, px_r, px_b = norm_box_to_px(box_norm, W, H)

    # Collect interior pixels (avoid 3px edges)
    margin = 3
    pixels = []
    for y in range(px_t + margin, px_b - margin, sample_step):
        for x in range(px_l + margin, px_r - margin, sample_step):
            pixels.append(sample_pixel(img, x, y))

    # Dominant colors via K-means
    dominant = kmeans_colors(pixels, k=top_k_colors)
    dominant_hex = [rgb_to_hex(*c) for c in dominant]

    # Gradient detection
    gradient = detect_gradient(img, px_l, px_t, px_r, px_b)

    # Border detection
    border = detect_border(img, px_l, px_t, px_r, px_b)

    # Sub-containers detection (title_strip vs full_card vs plain_text)
    sub_containers = detect_vertical_strips(img, px_l, px_t, px_r, px_b, W, H)

    # Background = most dominant color that appears in the center
    center_color = sample_pixel(img, (px_l + px_r) // 2, (px_t + px_b) // 2)
    bg_color = rgb_to_hex(*center_color)

    return {
        "box_norm": box_norm,
        "bg_color": bg_color,
        "gradient": gradient,
        "border": border,
        "sub_containers": sub_containers,
        "dominant_colors": dominant_hex,
        "pixel_region_px": [px_l, px_t, px_r, px_b],
        "canvas_size": [W, H],
    }


def profile_multiple_blocks(img_path: str, blocks: List[Dict]) -> List[Dict]:
    """Profile multiple blocks at once."""
    results = []
    for block in blocks:
        name = block.get("name", "unknown")
        box = block.get("box_norm", block.get("box", [0, 0, 1000, 1000]))
        print(f"  Profiling: {name} {box}")
        result = profile_block(img_path, box)
        result["name"] = name
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Auto Color/Gradient Profiler for PPT Blocks")
    parser.add_argument("image", help="Input slide PNG path")
    parser.add_argument("--box", nargs=4, type=float, metavar=("L", "T", "W", "H"),
                        help="0-1000 normalized box to profile")
    parser.add_argument("--blocks-json", help="JSON file with list of {name, box_norm} blocks")
    parser.add_argument("--step", type=int, default=4, help="Pixel sampling step")
    parser.add_argument("--colors", type=int, default=5, help="Number of dominant colors")
    parser.add_argument("-o", "--output", default=None, help="Save JSON result to file")
    args = parser.parse_args()

    if args.box:
        result = profile_block(args.image, list(args.box), sample_step=args.step, top_k_colors=args.colors)
        results = [result]
    elif args.blocks_json:
        with open(args.blocks_json) as f:
            blocks = json.load(f)
        results = profile_multiple_blocks(args.image, blocks)
    else:
        # Default: profile full slide in 5x5 grid
        print("[color_profiler] No box specified — sampling 5×5 grid of entire slide")
        results = []
        for row in range(5):
            for col in range(5):
                box = [col * 200, row * 200, 200, 200]
                r = profile_block(args.image, box, sample_step=8)
                r["name"] = f"grid_{row}_{col}"
                results.append(r)

    output_json = json.dumps(results, indent=2, ensure_ascii=False)
    print(output_json)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"\n[color_profiler] Results saved to: {args.output}")


if __name__ == "__main__":
    main()
