#!/usr/bin/env python3
"""Skill: Spacing & Grid - Normalized Spatial Layout and Grid Calculation Engine.

Calculates exact 0-1000 sub-coordinates, flex stacks, and multi-column alignment anchors.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


def calculate_grid_cells(
    parent_box: List[float],
    cols: int,
    rows: int = 1,
    gap_x: float = 16.0,
    gap_y: float = 16.0,
) -> List[List[float]]:
    """Partition a parent 0-1000 box into rows x cols cells with specified gaps."""
    l, t, w, h = parent_box
    if cols <= 0 or rows <= 0:
        return []

    total_gap_w = (cols - 1) * gap_x
    total_gap_h = (rows - 1) * gap_y
    cell_w = max(1.0, (w - total_gap_w) / float(cols))
    cell_h = max(1.0, (h - total_gap_h) / float(rows))

    cells = []
    for r in range(rows):
        for c in range(cols):
            cx = round(l + c * (cell_w + gap_x), 1)
            cy = round(t + r * (cell_h + gap_y), 1)
            cells.append([cx, cy, round(cell_w, 1), round(cell_h, 1)])
    return cells


def compute_two_column_baseline(
    top: float = 305.0,
    bottom: float = 925.0,
    left_margin: float = 26.0,
    right_margin: float = 26.0,
    gap: float = 16.0,
    left_ratio: float = 0.49,
) -> Dict[str, Any]:
    """Derive perfectly aligned left and right column root container bounding boxes."""
    total_w = 1000.0 - left_margin - right_margin
    content_h = bottom - top
    usable_w = total_w - gap
    left_w = round(usable_w * left_ratio, 1)
    right_w = round(usable_w - left_w, 1)
    right_l = round(left_margin + left_w + gap, 1)

    return {
        "left_column": [round(left_margin, 1), round(top, 1), left_w, round(content_h, 1)],
        "right_column": [right_l, round(top, 1), right_w, round(content_h, 1)],
        "top_baseline": round(top, 1),
        "bottom_baseline": round(bottom, 1),
        "height": round(content_h, 1),
    }


def distribute_vertical_sections(
    container_top: float,
    container_height: float,
    count: int,
    header_h: float = 76.0,
    footer_h: float = 75.0,
    top_margin: float = 24.0,
    bottom_margin: float = 20.0,
    min_gap_y: float = 30.0,
) -> List[Dict[str, float]]:
    """Calculate balanced vertical section tops and heights without giant void gaps."""
    if count <= 0:
        return []

    content_start_y = container_top + header_h + top_margin
    content_end_y = container_top + container_height - footer_h - bottom_margin
    available_h = content_end_y - content_start_y

    total_gaps_h = (count - 1) * min_gap_y
    remaining_h = available_h - total_gaps_h
    section_h = max(40.0, remaining_h / float(count))

    sections = []
    current_y = content_start_y
    for i in range(count):
        sections.append({
            "index": i + 1,
            "top": round(current_y, 1),
            "height": round(section_h, 1),
            "bottom": round(current_y + section_h, 1)
        })
        current_y += section_h + min_gap_y

    return sections


def main():
    parser = argparse.ArgumentParser(description="Skill: Spacing & Grid Calculator")
    parser.add_argument("--grid", nargs=4, type=float, metavar=("L", "T", "W", "H"), help="Parent box")
    parser.add_argument("--cols", type=int, default=3, help="Number of columns")
    parser.add_argument("--rows", type=int, default=1, help="Number of rows")
    parser.add_argument("--gap-x", type=float, default=16.0, help="Horizontal gap")
    parser.add_argument("--gap-y", type=float, default=16.0, help="Vertical gap")
    parser.add_argument("--columns-baseline", action="store_true", help="Calculate standard 2-column baseline")

    args = parser.parse_args()

    if args.columns_baseline:
        res = compute_two_column_baseline()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.grid:
        cells = calculate_grid_cells(args.grid, args.cols, args.rows, args.gap_x, args.gap_y)
        print(json.dumps({"cells": cells}, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
