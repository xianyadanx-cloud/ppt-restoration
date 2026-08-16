"""PPTX Document Structure & DOM Inspector.

Enables Coding Agents to inspect PPTX slide hierarchies, shape types,
coordinates, text content, tables, and charts directly from the terminal.
"""

import sys
import os
import argparse
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def inspect_pptx(pptx_path: str, verbose: bool = False):
    if not os.path.exists(pptx_path):
        print(f"[Error] PPTX file not found: {pptx_path}")
        sys.exit(1)

    prs = Presentation(pptx_path)
    width_in = prs.slide_width.inches
    height_in = prs.slide_height.inches

    print("=" * 60)
    print(f"📄 PPTX Structure Inspection: {pptx_path}")
    print(f"📐 Dimensions: {width_in:.2f} x {height_in:.2f} inches (Aspect Ratio: {width_in/height_in:.2f}:1)")
    print(f"📑 Total Slides: {len(prs.slides)}")
    print("=" * 60)

    for s_idx, slide in enumerate(prs.slides, 1):
        print(f"\n--- Slide #{s_idx} ({len(slide.shapes)} shapes) ---")
        for sh_idx, shape in enumerate(slide.shapes, 1):
            # Calculate 0-1000 normalized coordinates
            l_1000 = (shape.left.inches / width_in) * 1000 if width_in > 0 else 0
            t_1000 = (shape.top.inches / height_in) * 1000 if height_in > 0 else 0
            w_1000 = (shape.width.inches / width_in) * 1000 if width_in > 0 else 0
            h_1000 = (shape.height.inches / height_in) * 1000 if height_in > 0 else 0

            shape_type_name = str(shape.shape_type).split(".")[-1]
            extra_info = []

            # Text content
            if shape.has_text_frame:
                text_snippet = " | ".join(
                    [p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip()]
                )
                if len(text_snippet) > 60:
                    text_snippet = text_snippet[:57] + "..."
                if text_snippet:
                    extra_info.append(f'text="{text_snippet}"')

            # Table info
            if shape.has_table:
                table = shape.table
                extra_info.append(f"table={len(table.rows)}x{len(table.columns)}")

            # Chart info
            if shape.has_chart:
                chart = shape.chart
                extra_info.append(f"chart_type={str(chart.chart_type).split('.')[-1]}")

            info_str = " | ".join(extra_info) if extra_info else "container/shape"
            print(f"  [{sh_idx:02d}] {shape_type_name:<18} Box: [{l_1000:5.1f}, {t_1000:5.1f}, {w_1000:5.1f}, {h_1000:5.1f}]  -> {info_str}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Inspect PPTX slide hierarchy and DOM structure.")
    parser.add_argument("pptx_file", help="Path to .pptx file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    inspect_pptx(args.pptx_file, args.verbose)


if __name__ == "__main__":
    main()
