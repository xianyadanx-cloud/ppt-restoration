#!/usr/bin/env python3
"""Skill: Element Profiler - Micro Element Geometry & Property Profiler Engine.

Performs mathematical shape classification, color extraction, and typography estimation on image ROIs.
"""

import argparse
import json
import math
import os
import sys
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageStat


def analyze_element_roi(img: Image.Image) -> Dict[str, Any]:
    """Analyze a cropped PIL Image ROI to classify shape and extract dominant colors."""
    w, h = img.size
    if w == 0 or h == 0:
        return {"shape": "UNKNOWN", "colors": []}

    aspect_ratio = float(w) / float(h)
    rgb_img = img.convert("RGB")
    gray = img.convert("L")

    # 1. Edge & Foreground Bounding
    pixels = list(gray.getdata())
    min_val, max_val = min(pixels), max(pixels)
    contrast = max_val - min_val

    # 2. Simple Circularity Approximation via mask moments
    # Threshold at Otsu or mid-gray
    thresh = (min_val + max_val) // 2
    fg_points = []
    for y in range(h):
        for x in range(w):
            val = gray.getpixel((x, y))
            # Assume foreground is darker or different from background
            if abs(val - 255) > 40:
                fg_points.append((x, y))

    area = len(fg_points)
    if area == 0:
        return {
            "shape": "TEXT_PLAIN",
            "aspect_ratio": round(aspect_ratio, 2),
            "primary_color": "#000000",
        }

    # Bounding of foreground
    min_x = min(pt[0] for pt in fg_points)
    max_x = max(pt[0] for pt in fg_points)
    min_y = min(pt[1] for pt in fg_points)
    max_y = max(pt[1] for pt in fg_points)
    bw = max_x - min_x + 1
    bh = max_y - min_y + 1
    box_aspect = float(bw) / float(bh) if bh > 0 else 1.0

    # Calculate perimeter (boundary points)
    fg_set = set(fg_points)
    perimeter_points = 0
    for x, y in fg_points:
        # If any 4-neighbor is not in fg_set, it's a boundary point
        if (x + 1, y) not in fg_set or (x - 1, y) not in fg_set or (x, y + 1) not in fg_set or (x, y - 1) not in fg_set:
            perimeter_points += 1

    perimeter = max(1, perimeter_points)
    circularity = (4.0 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0

    # 3. Classify Shape
    if 0.82 <= box_aspect <= 1.22 and circularity >= 0.70:
        shape_type = "SHAPE_CIRCLE"
    elif box_aspect > 1.4 and circularity >= 0.55:
        shape_type = "SHAPE_PILL"
    elif box_aspect < 0.7 and circularity >= 0.55:
        shape_type = "SHAPE_PILL_VERTICAL"
    elif contrast < 30:
        shape_type = "TEXT_PLAIN"
    else:
        shape_type = "SHAPE_RECT_ROUNDED"

    # 4. Color sampling
    stat = ImageStat.Stat(rgb_img)
    avg_rgb = [int(c) for c in stat.mean[:3]]
    hex_color = f"#{avg_rgb[0]:02X}{avg_rgb[1]:02X}{avg_rgb[2]:02X}"

    return {
        "shape": shape_type,
        "aspect_ratio": round(aspect_ratio, 2),
        "circularity": round(circularity, 3),
        "dimensions": [w, h],
        "primary_color": hex_color,
    }


def profile_crop_file(image_path: str, box: Optional[List[int]] = None) -> Dict[str, Any]:
    """Profile an image crop by path and optional pixel bounding box."""
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}

    img = Image.open(image_path)
    if box and len(box) == 4:
        img = img.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))

    return analyze_element_roi(img)


def main():
    parser = argparse.ArgumentParser(description="Skill: Element Profiler")
    parser.add_argument("image", help="Path to cropped element image")
    parser.add_argument("--box", nargs=4, type=int, help="Optional bounding box [X, Y, W, H]")
    parser.add_argument("-o", "--output", help="Save manifest to JSON file")
    args = parser.parse_args()

    result = profile_crop_file(args.image, args.box)
    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    print(out_json)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"\n[Saved manifest to: {args.output}]")


if __name__ == "__main__":
    main()
