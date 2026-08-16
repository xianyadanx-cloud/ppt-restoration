"""Deterministic PPTX Element Property Extractor and Ground Truth Comparison Tool (tools/compare_properties.py)

Extracts PPTX shape/text properties directly from OpenXML DOM and compares against Ground Truth pixel measurements.
"""

import os
import sys
from typing import Dict, List, Any
from pptx import Presentation
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas


def extract_pptx_elements(pptx_path: str) -> List[Dict[str, Any]]:
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    sw = prs.slide_width
    sh = prs.slide_height

    elements = []
    for idx, shape in enumerate(slide.shapes):
        l = round((shape.left / sw) * 1000.0, 1)
        t = round((shape.top / sh) * 1000.0, 1)
        w = round((shape.width / sw) * 1000.0, 1)
        h = round((shape.height / sh) * 1000.0, 1)

        elem_info = {
            "index": idx + 1,
            "box": [l, t, w, h],
            "type": shape.shape_type,
            "text": "",
            "font_size": None,
            "bold": False,
            "align": "left",
            "font_color": None,
            "fill": None,
        }

        # Check Fill
        try:
            if shape.fill and shape.fill.type == 1:
                elem_info["fill"] = f"#{shape.fill.fore_color.rgb}"
        except Exception:
            pass

        # Check Text Frame
        if shape.has_text_frame:
            tf = shape.text_frame
            full_text = tf.text.strip()
            elem_info["text"] = full_text.replace("\n", " | ")
            if tf.paragraphs:
                p0 = tf.paragraphs[0]
                align_str = "left"
                if p0.alignment == 2:
                    align_str = "center"
                elif p0.alignment == 3:
                    align_str = "right"
                elem_info["align"] = align_str

                if p0.runs:
                    r0 = p0.runs[0]
                    elem_info["font_size"] = r0.font.size.pt if r0.font.size else None
                    elem_info["bold"] = r0.font.bold or False
                    if r0.font.color and r0.font.color.rgb:
                        elem_info["font_color"] = f"#{r0.font.color.rgb}"

        if elem_info["text"] or elem_info["fill"]:
            elements.append(elem_info)

    return elements


def measure_ground_truth_block4(image_path: str) -> Dict[str, Any]:
    raw = Image.open(image_path).convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw)
    canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    p = canvas.load()

    # 1. Ground Truth Title: "核心战役完成度全景"
    # Find exact bounding box of characters in canvas
    t_pts = []
    for y in range(250, 360):
        for x in range(50, 700):
            r, g, b = p[x, y]
            if r < 60 and g < 60 and b < 60:
                t_pts.append((x, y))

    title_box = [round(min(pt[0] for pt in t_pts)/1.44, 1), round(min(pt[1] for pt in t_pts)/0.81, 1),
                 round((max(pt[0] for pt in t_pts) - min(pt[0] for pt in t_pts))/1.44, 1),
                 round((max(pt[1] for pt in t_pts) - min(pt[1] for pt in t_pts))/0.81, 1)] if t_pts else []

    # Title character height in px -> pt
    h_px = (max(pt[1] for pt in t_pts) - min(pt[1] for pt in t_pts)) if t_pts else 0
    title_pt = round(h_px * 0.667 * 1.5, 1)

    # 2. Ground Truth Blue Header Bar
    h_pts = []
    for y in range(310, 420):
        for x in range(50, 700):
            r, g, b = p[x, y]
            if b > 140 and r < 80 and g > 60:
                h_pts.append((x, y, (r, g, b)))

    header_box = [round(min(pt[0] for pt in h_pts)/1.44, 1), round(min(pt[1] for pt in h_pts)/0.81, 1),
                  round((max(pt[0] for pt in h_pts) - min(pt[0] for pt in h_pts))/1.44, 1),
                  round((max(pt[1] for pt in h_pts) - min(pt[1] for pt in h_pts))/0.81, 1)] if h_pts else []

    return {
        "title": {
            "text": "核心战役完成度全景",
            "box_0_1000": title_box,
            "center_x": round((title_box[0] + title_box[2]/2), 1) if title_box else 0,
            "font_size_pt": 20.0,
            "bold": True,
            "align": "center",
            "font_color": "#000000",
        },
        "header_bar": {
            "box_0_1000": header_box,
            "gradient_top": "#428BD6",
            "gradient_bottom": "#165096",
            "columns": [
                {"name": "项目名称", "align": "left", "size_pt": 12.0, "bold": True},
                {"name": "目标值", "align": "center", "size_pt": 12.0, "bold": True},
                {"name": "实际值", "align": "center", "size_pt": 12.0, "bold": True},
                {"name": "整体完成率", "align": "center", "size_pt": 12.0, "bold": True},
            ]
        }
    }


import argparse
import json

def compare_and_report(pptx_elems: List[Dict[str, Any]], gt_data: Dict[str, Any], json_output: bool = False):
    report = []
    
    # Check title
    gt_t = gt_data.get("title", {})
    gt_text = gt_t.get("text", "")
    
    # Find matching pptx elem by text
    pt_elem = next((e for e in pptx_elems if gt_text in e.get("text", "")), None)
    
    if pt_elem:
        # Build comparison
        diff = {
            "element": gt_text,
            "box": {"pptx": pt_elem["box"], "gt": gt_t["box_0_1000"]},
            "font_size": {"pptx": pt_elem["font_size"], "gt": gt_t["font_size_pt"]},
            "align": {"pptx": pt_elem["align"], "gt": gt_t["align"]}
        }
        report.append(diff)
        
    if json_output:
        print(json.dumps({"diff_matrix": report}, ensure_ascii=False, indent=2))
        return

    print("=" * 80)
    print(f"{'Element':<25} | {'Property':<15} | {'PPTX (Actual)':<20} | {'Ground Truth':<20}")
    print("-" * 80)
    for item in report:
        elem_name = item["element"][:23]
        
        # Box
        p_box = str(item["box"]["pptx"])
        g_box = str(item["box"]["gt"])
        flag = "❌" if p_box != g_box else "✅"
        print(f"{elem_name:<25} | {'Box [L,T,W,H]':<15} | {p_box:<20} | {g_box:<20} {flag}")
        
        # Font size
        p_size = str(item["font_size"]["pptx"])
        g_size = str(item["font_size"]["gt"])
        flag = "❌" if p_size != g_size else "✅"
        print(f"{'':<25} | {'Font Size':<15} | {p_size:<20} | {g_size:<20} {flag}")
        
        # Align
        p_al = str(item["align"]["pptx"])
        g_al = str(item["align"]["gt"])
        flag = "❌" if p_al != g_al else "✅"
        print(f"{'':<25} | {'Alignment':<15} | {p_al:<20} | {g_al:<20} {flag}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="PPTX vs Ground Truth Property Comparer")
    parser.add_argument("pptx_path", help="Path to the generated PPTX file")
    parser.add_argument("image_path", help="Path to the Ground Truth PNG image")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    if not args.json:
        print("=" * 80)
        print("🔍 PPTX 元素属性提取与原图确定性对比报告")
        print("=" * 80)

    pptx_elems = extract_pptx_elements(args.pptx_path)
    
    # We use the existing hardcoded block4 measurement as the prototype for GT extraction
    gt_data = measure_ground_truth_block4(args.image_path)
    
    compare_and_report(pptx_elems, gt_data, json_output=args.json)

if __name__ == "__main__":
    main()
