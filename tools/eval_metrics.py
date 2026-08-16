#!/usr/bin/env python3
"""Automated Multi-Agent Evaluation & Structural Quality Metrics Engine.

Calculates:
1. Structural Similarity Index (SSIM) & Mean Squared Error (MSE)
2. Native PPTX DOM Tree Verification (Ensures PICTURE count == 0)
3. Structured Review Report JSON output for In-Place Healing Loop
"""

import argparse
import json
import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image


def calculate_mse_and_ssim(img1: Image.Image, img2: Image.Image) -> Tuple[float, float]:
    """Calculate MSE and simple Structural Similarity Index (SSIM) between two PIL images."""
    # Resize to common size
    target_size = (512, 288)
    i1 = img1.convert("L").resize(target_size, Image.Resampling.BILINEAR)
    i2 = img2.convert("L").resize(target_size, Image.Resampling.BILINEAR)

    pixels1 = list(i1.getdata())
    pixels2 = list(i2.getdata())
    n = len(pixels1)
    if n == 0:
        return 0.0, 1.0

    # 1. MSE
    sum_sq_diff = sum((p1 - p2) ** 2 for p1, p2 in zip(pixels1, pixels2))
    mse = sum_sq_diff / float(n)

    # 2. SSIM approximation
    mean1 = sum(pixels1) / float(n)
    mean2 = sum(pixels2) / float(n)

    var1 = sum((p1 - mean1) ** 2 for p1 in pixels1) / float(n)
    var2 = sum((p2 - mean2) ** 2 for p2 in pixels2) / float(n)
    cov12 = sum((p1 - mean1) * (p2 - mean2) for p1, p2 in zip(pixels1, pixels2)) / float(n)

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    numerator = (2 * mean1 * mean2 + c1) * (2 * cov12 + c2)
    denominator = (mean1 ** 2 + mean2 ** 2 + c1) * (var1 + var2 + c2)

    ssim = numerator / denominator if denominator != 0 else 1.0
    ssim = max(0.0, min(1.0, ssim))
    return round(mse, 2), round(ssim, 4)


def inspect_dom_picture_count(pptx_path: str) -> Dict[str, Any]:
    """Inspect pptx XML DOM tree directly to count PICTURE (p:pic) elements."""
    if not os.path.exists(pptx_path):
        return {"error": f"File not found: {pptx_path}", "picture_count": -1, "status": "FAIL"}

    pic_count = 0
    shape_count = 0
    table_count = 0
    textbox_count = 0

    try:
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide_files = [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
            for s_file in slide_files:
                xml_content = z.read(s_file)
                root = ET.fromstring(xml_content)
                # Count p:pic tags
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag == "pic":
                        pic_count += 1
                    elif tag == "sp":
                        shape_count += 1
                    elif tag == "tbl":
                        table_count += 1
                    elif tag == "txBody":
                        textbox_count += 1

        is_native_pass = (pic_count == 0)
        return {
            "picture_count": pic_count,
            "shape_count": shape_count,
            "table_count": table_count,
            "textbox_count": textbox_count,
            "status": "PASS" if is_native_pass else "FAIL",
            "is_pure_vector": is_native_pass,
        }
    except Exception as e:
        return {"error": str(e), "picture_count": -1, "status": "FAIL"}


def evaluate_rendering(
    rendered_img_path: str,
    ground_truth_img_path: str,
    pptx_path: Optional[str] = None,
    crop_box: Optional[List[float]] = None,
    block_id: Optional[int] = None,
    threshold_ssim: float = 0.85,
) -> Dict[str, Any]:
    """Perform comprehensive automated evaluation and return structured review report."""
    if not os.path.exists(rendered_img_path) or not os.path.exists(ground_truth_img_path):
        return {
            "passed": False,
            "error": "Image file not found for evaluation",
            "ssim_score": 0.0,
            "mse_score": 9999.0,
        }

    img_render = Image.open(rendered_img_path)
    img_gt = Image.open(ground_truth_img_path)

    # Crop to 0-1000 sub-region if box provided
    if crop_box and len(crop_box) == 4:
        l, t, w, h = crop_box
        # Crop render
        rw, rh = img_render.size
        r_crop = img_render.crop((int(l * rw / 1000), int(t * rh / 1000), int((l + w) * rw / 1000), int((t + h) * rh / 1000)))
        # Crop gt
        gw, gh = img_gt.size
        gt_crop = img_gt.crop((int(l * gw / 1000), int(t * gh / 1000), int((l + w) * gw / 1000), int((t + h) * gh / 1000)))
        mse, ssim = calculate_mse_and_ssim(r_crop, gt_crop)
    else:
        mse, ssim = calculate_mse_and_ssim(img_render, img_gt)

    dom_res = inspect_dom_picture_count(pptx_path) if pptx_path else {"status": "PASS", "picture_count": 0}

    passed = (ssim >= threshold_ssim) and (dom_res.get("status") == "PASS")

    report = {
        "block_id": block_id,
        "passed": passed,
        "ssim_score": ssim,
        "mse_score": mse,
        "threshold_ssim": threshold_ssim,
        "dom_check": dom_res,
        "issues": []
    }

    if dom_res.get("picture_count", 0) > 0:
        report["issues"].append({
            "type": "DOM_VIOLATION",
            "message": f"Detected {dom_res['picture_count']} PICTURE elements. Gate 4 strictly requires 0 pictures (100% native vectors)."
        })

    if ssim < threshold_ssim:
        report["issues"].append({
            "type": "VISUAL_DIVERGENCE",
            "message": f"Visual SSIM score {ssim:.4f} is below target threshold {threshold_ssim:.2f}. In-place healing recommended."
        })

    return report


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Automated Evaluation Engine")
    parser.add_argument("render", help="Path to rendered slide image or PPTX")
    parser.add_argument("gt", help="Path to ground truth image")
    parser.add_argument("--pptx", help="Path to target PPTX file for DOM inspection")
    parser.add_argument("--crop-box", nargs=4, type=float, help="0-1000 bounding box [L T W H]")
    parser.add_argument("--block-id", type=int, default=1, help="Block ID")
    parser.add_argument("--threshold", type=float, default=0.85, help="SSIM passing threshold")
    parser.add_argument("-o", "--output", help="Save review_report.json to path")

    args = parser.parse_args()
    report = evaluate_rendering(
        rendered_img_path=args.render,
        ground_truth_img_path=args.gt,
        pptx_path=args.pptx,
        crop_box=args.crop_box,
        block_id=args.block_id,
        threshold_ssim=args.threshold,
    )

    json_str = json.dumps(report, indent=2, ensure_ascii=False)
    print(json_str)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"\n[Report saved to: {args.output}]")


if __name__ == "__main__":
    main()
