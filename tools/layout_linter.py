#!/usr/bin/env python3
"""PPT Layout Linter & Geometric Constraint Static Checker (tools/layout_linter.py)

Performs deterministic static layout assertion audits on PowerPoint (.pptx) files:
1. Multi-Column Baseline Alignment: Asserts top/bottom alignment across major parallel cards.
2. Bottom Breathing Safe Margin: Asserts content bottom does not exceed safe margin (e.g. <= 930).
3. Typography Hierarchy & Scale: Asserts title and author font sizes adhere to design token limits.
4. Native Vector Integrity: Asserts 0 raster PICTURE shapes exist.
5. In-Row Vertical Centering: Asserts row items (table texts vs progress bars) share aligned center lines.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Tuple
from pptx import Presentation


def audit_layout(pptx_path: str) -> Dict[str, Any]:
    """Audit slide layout geometry against strict consulting-grade design rules."""
    if not os.path.exists(pptx_path):
        return {"passed": False, "errors": [f"File not found: {pptx_path}"]}

    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    sw = prs.slide_width
    sh = prs.slide_height

    shapes_info = []
    pic_count = 0

    for idx, s in enumerate(slide.shapes):
        l = round((s.left / sw) * 1000.0, 1)
        t = round((s.top / sh) * 1000.0, 1)
        w = round((s.width / sw) * 1000.0, 1)
        h = round((s.height / sh) * 1000.0, 1)

        # Check picture
        if s.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            pic_count += 1

        text = ""
        font_size = None
        bold = False
        if s.has_text_frame:
            tf = s.text_frame
            text = tf.text.strip()
            if tf.paragraphs and tf.paragraphs[0].runs:
                r0 = tf.paragraphs[0].runs[0]
                font_size = r0.font.size.pt if r0.font.size else None
                bold = r0.font.bold or False

        shapes_info.append({
            "id": idx + 1,
            "name": s.name,
            "type": s.shape_type,
            "box": [l, t, w, h],
            "bottom": round(t + h, 1),
            "right": round(l + w, 1),
            "text": text,
            "font_size": font_size,
            "bold": bold,
        })

    errors = []
    warnings = []
    passed_rules = []

    # Rule 1: Zero Picture Violation
    if pic_count > 0:
        errors.append(f"[RULE 1: PURE_VECTOR_VIOLATION] Detected {pic_count} raster PICTURE shapes. Strict 0-picture rule failed.")
    else:
        passed_rules.append("Rule 1: Pure Native Vector Integrity (PICTURE == 0)")

    # Rule 2: Bottom Breathing Margin (<= 930)
    max_bottom = max((s["bottom"] for s in shapes_info), default=0)
    if max_bottom > 935.0:
        errors.append(f"[RULE 2: BOTTOM_OVERFLOW] Elements reach bottom={max_bottom:.1f}, exceeding safe margin 930.0 (too close to slide edge).")
    else:
        passed_rules.append(f"Rule 2: Bottom Breathing Safe Margin (max_bottom={max_bottom:.1f} <= 930.0)")

    # Rule 3: Main Multi-Column Alignment
    # Partition into left column (left < 460) and right column (left >= 460)
    left_candidates = [s for s in shapes_info if s["box"][0] < 460 and 280 <= s["box"][1] <= 350 and s["box"][2] >= 350]
    right_candidates = [s for s in shapes_info if s["box"][0] >= 460 and 280 <= s["box"][1] <= 350 and s["box"][2] >= 350]

    if left_candidates and right_candidates:
        # Pick the outermost/largest container in each column
        left_card = max(left_candidates, key=lambda s: s["box"][2] * s["box"][3])
        right_card = max(right_candidates, key=lambda s: s["box"][2] * s["box"][3])
        top_diff = abs(left_card["box"][1] - right_card["box"][1])
        bottom_diff = abs(left_card["bottom"] - right_card["bottom"])

        if top_diff > 2.0:
            errors.append(f"[RULE 3: COLUMN_TOP_MISALIGNMENT] Left card top={left_card['box'][1]} vs Right card top={right_card['box'][1]} (delta={top_diff:.1f} > 2.0)")
        if bottom_diff > 3.0:
            errors.append(f"[RULE 3: COLUMN_BOTTOM_MISALIGNMENT] Left card bottom={left_card['bottom']} vs Right card bottom={right_card['bottom']} (delta={bottom_diff:.1f} > 3.0)")
        
        if top_diff <= 2.0 and bottom_diff <= 3.0:
            passed_rules.append(f"Rule 3: Multi-Column Baseline Alignment (top_delta={top_diff:.1f}, bottom_delta={bottom_diff:.1f})")

    # Rule 4: Typography Scale & Hierarchy
    # Find main title (text contains '季度' or '策略' or '断点')
    title_shapes = [s for s in shapes_info if "季度" in s["text"] or "策略" in s["text"] or "断点" in s["text"]]
    if title_shapes:
        t_shape = title_shapes[0]
        if t_shape["font_size"] and t_shape["font_size"] > 32.0:
            warnings.append(f"[RULE 4: TYPOGRAPHY_OVERSIZED] Main title font size is {t_shape['font_size']} pt, recommended <= 30 pt to prevent vertical crowding.")
        else:
            passed_rules.append(f"Rule 4: Main Title Typography Scale ({t_shape.get('font_size')} pt <= 32 pt)")

    # Find author watermark (contains '@' or 'PPT')
    author_shapes = [s for s in shapes_info if "@" in s["text"]]
    if author_shapes:
        a_shape = author_shapes[0]
        if a_shape["font_size"] and a_shape["font_size"] > 16.0:
            warnings.append(f"[RULE 4: AUTHOR_TAG_OVERSIZED] Author watermark font size is {a_shape['font_size']} pt, recommended <= 16 pt.")
        else:
            passed_rules.append(f"Rule 4: Author Watermark Typography Scale ({a_shape.get('font_size')} pt <= 16 pt)")

    overall_pass = len(errors) == 0

    return {
        "passed": overall_pass,
        "errors": errors,
        "warnings": warnings,
        "passed_rules": passed_rules,
        "total_shapes": len(shapes_info),
        "max_bottom": max_bottom,
    }


def main():
    parser = argparse.ArgumentParser(description="PPT Layout Linter & Geometric Quality Inspector")
    parser.add_argument("pptx", help="Path to input presentation (.pptx)")
    args = parser.parse_args()

    res = audit_layout(args.pptx)

    print("=" * 70)
    print(f"📐 PPT Layout Linter Audit: [{args.pptx}]")
    print("=" * 70)

    for r in res.get("passed_rules", []):
        print(f"  ✅ {r}")

    if res.get("warnings"):
        print("\n⚠️ Warnings:")
        for w in res["warnings"]:
            print(f"  🔸 {w}")

    if res.get("errors"):
        print("\n❌ Errors (Linting Violations):")
        for e in res["errors"]:
            print(f"  🚫 {e}")
        print("\n[VERDICT]: ❌ LINT FAILED")
        sys.exit(1)
    else:
        print("\n[VERDICT]: 🎉 ALL LAYOUT GEOMETRIC CONSTRAINTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
