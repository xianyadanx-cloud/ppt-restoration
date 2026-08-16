#!/usr/bin/env python3
"""Skill: Vector Builder - Compiles Manifest JSON into Native SlideBuilder Python Code."""

import argparse
import json
import sys
from typing import Any, Dict, List


def generate_python_block_code(manifest: Dict[str, Any]) -> str:
    """Generate a clean, self-contained Python function from a Block Manifest JSON."""
    block_id = manifest.get("block_id", 1)
    func_name = manifest.get("function_name", f"add_block_{block_id}_section")
    doc = manifest.get("name", f"Block {block_id}")

    lines = [
        f"def {func_name}(builder: SlideBuilder) -> None:",
        f'    """Render {doc} (Compiled via vector-builder skill)."""',
    ]

    # Render Container if specified
    container = manifest.get("container")
    if container:
        c_box = container.get("box", [0, 0, 1000, 1000])
        c_bg = container.get("bg_color", "#FFFFFF")
        c_border = container.get("border_color", "transparent")
        c_radius = container.get("radius", True)
        lines.append(f"    # Root Container")
        lines.append(f"    builder.add_card(box={c_box}, bg_color='{c_bg}', border_color='{c_border}', radius={c_radius})")

    # Render Sub-elements
    elements = manifest.get("elements", [])
    for elem in elements:
        e_type = elem.get("type", "TEXT_PLAIN")
        e_box = elem.get("box", [0, 0, 100, 100])
        e_text = elem.get("text", "")
        e_bg = elem.get("bg_color", "transparent")
        e_fg = elem.get("text_color", "#000000")
        e_size = elem.get("font_size", 12)
        e_bold = elem.get("bold", False)

        if e_type in ["SHAPE_CIRCLE", "SHAPE_PILL"]:
            lines.append(f"    builder.add_badge(box={e_box}, text='{e_text}', bg_color='{e_bg}', text_color='{e_fg}', font_size={e_size}, bold={e_bold})")
        elif e_type in ["SHAPE_RECT_ROUNDED", "SHAPE_RECT_SHARP"]:
            e_border = elem.get("border_color", "transparent")
            lines.append(f"    builder.add_card(box={e_box}, bg_color='{e_bg}', border_color='{e_border}', radius={(e_type == 'SHAPE_RECT_ROUNDED')})")
        elif e_type == "TEXT_PLAIN":
            lines.append(f"    builder.add_textbox(box={e_box}, text='{e_text}', font_size={e_size}, font_color='{e_fg}', bold={e_bold}, auto_fit_font=True)")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Skill: Vector Builder")
    parser.add_argument("manifest", help="Path to manifest JSON file")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    code = generate_python_block_code(data)
    print(code)


if __name__ == "__main__":
    main()
