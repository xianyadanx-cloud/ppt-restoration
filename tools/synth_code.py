"""synth_code.py — Declarative JSON Specification to Native Python PPTX Code Synthesizer

Transforms structured Block Specification JSONs directly into clean, modular Python scripts
that use SlideBuilder from pptx_helper.py.

Eliminates manual boilerplate code writing and guarantees 100% vector-only execution.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def sanitize_func_name(name: str) -> str:
    """Convert Chinese or arbitrary name to valid python function identifier."""
    # Mapping common block types to standard English function names
    mapping = {
        "header": "add_header_section",
        "summary": "add_summary_banner_section",
        "kpi": "add_kpi_section",
        "table": "add_table_section",
        "clipboard": "add_clipboard_section",
        "strategy": "add_strategy_card_section",
        "footer": "add_footer_section",
    }
    name_lower = name.lower()
    for k, v in mapping.items():
        if k in name_lower:
            return v
    # Fallback to ascii alphanumeric
    clean = "".join(c if c.isalnum() else "_" for c in name).strip("_")
    return f"add_{clean}_section" if clean else "add_custom_section"


def synth_element_code(elem: Dict[str, Any], indent: str = "    ") -> List[str]:
    """Synthesize SlideBuilder call code for a single element definition."""
    lines = []
    elem_type = elem.get("type", "card").lower()
    box = elem.get("box_norm", elem.get("box", [50, 50, 100, 100]))
    name = elem.get("name", elem_type)

    lines.append(f"{indent}# --- {name} ({elem_type}) ---")

    if elem_type in ("card", "solid_card", "container"):
        bg = elem.get("bg_color", elem.get("bg", "#FFFFFF"))
        border = elem.get("border_color", elem.get("border", "transparent"))
        border_w = elem.get("border_width_pt", elem.get("border_width", 1.0))
        radius = elem.get("radius", True)
        lines.append(f"{indent}builder.add_card(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    bg_color=\"{bg}\",")
        if border != "transparent":
            lines.append(f"{indent}    border_color=\"{border}\",")
            lines.append(f"{indent}    border_width_pt={border_w},")
        lines.append(f"{indent}    radius={radius},")
        lines.append(f"{indent})")

    elif elem_type in ("gradient_card", "gradient"):
        grad = elem.get("gradient", {})
        colors = elem.get("gradient_colors", [s.get("color", "#2563EB") for s in grad.get("stops", [])] or ["#2563EB", "#60A5FA"])
        angle = elem.get("gradient_angle", 0.0 if grad.get("direction") == "horizontal" else 90.0)
        radius = elem.get("radius", True)
        lines.append(f"{indent}builder.add_card(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    gradient_colors={colors},")
        lines.append(f"{indent}    gradient_angle={angle},")
        lines.append(f"{indent}    border_color=\"transparent\",")
        lines.append(f"{indent}    radius={radius},")
        lines.append(f"{indent})")

    elif elem_type in ("badge", "pill", "capsule"):
        text = elem.get("text", elem.get("content", ""))
        bg = elem.get("bg_color", elem.get("bg", "#2563EB"))
        color = elem.get("text_color", elem.get("color", "#FFFFFF"))
        border = elem.get("border_color", "transparent")
        font_size = elem.get("font_size_pt", elem.get("font_size", 9.5))
        bold = elem.get("bold", True)
        lines.append(f"{indent}builder.add_badge(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    text=\"{text}\",")
        lines.append(f"{indent}    bg_color=\"{bg}\",")
        if border != "transparent":
            lines.append(f"{indent}    border_color=\"{border}\",")
        lines.append(f"{indent}    text_color=\"{color}\",")
        lines.append(f"{indent}    font_size={font_size},")
        lines.append(f"{indent}    bold={bold},")
        lines.append(f"{indent})")

    elif elem_type in ("text", "textbox", "title", "heading"):
        text = elem.get("text", elem.get("content", ""))
        color = elem.get("color", elem.get("font_color", "#0F172A"))
        size = elem.get("font_size_pt", elem.get("font_size", 14))
        bold = elem.get("bold", False)
        align = elem.get("align", "left")
        wrap = elem.get("word_wrap", True)
        lines.append(f"{indent}builder.add_textbox(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    text=\"{text}\",")
        lines.append(f"{indent}    font_size={size},")
        lines.append(f"{indent}    font_color=\"{color}\",")
        lines.append(f"{indent}    bold={bold},")
        if align != "left":
            lines.append(f"{indent}    align=\"{align}\",")
        if not wrap:
            lines.append(f"{indent}    word_wrap=False,")
        lines.append(f"{indent})")

    elif elem_type in ("progress_bar", "progress"):
        pct = elem.get("pct", 0.8)
        text = elem.get("text", f"{int(pct*100)}%")
        bar_color = elem.get("bar_color", "#C2410C")
        bg_color = elem.get("bg_color", "#FCE4D6")
        lines.append(f"{indent}builder.add_progress_bar(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    pct={pct},")
        lines.append(f"{indent}    text=\"{text}\",")
        lines.append(f"{indent}    bar_color=\"{bar_color}\",")
        lines.append(f"{indent}    bg_color=\"{bg_color}\",")
        lines.append(f"{indent}    node_glow={elem.get('node_glow', True)},")
        lines.append(f"{indent})")

    elif elem_type == "table":
        headers = elem.get("headers", ["Column 1", "Column 2"])
        rows = elem.get("rows", [["A", "B"], ["C", "D"]])
        widths = elem.get("col_widths", None)
        header_bg = elem.get("header_bg", "#1D64B2")
        lines.append(f"{indent}builder.add_table(")
        lines.append(f"{indent}    box={box},")
        lines.append(f"{indent}    headers={headers},")
        lines.append(f"{indent}    rows={rows},")
        if widths:
            lines.append(f"{indent}    col_widths={widths},")
        lines.append(f"{indent}    header_bg=\"{header_bg}\",")
        lines.append(f"{indent}    header_color=\"#FFFFFF\",")
        lines.append(f"{indent})")

    return lines


def synth_block_function(block_def: Dict[str, Any]) -> str:
    """Synthesize a complete Python block function definition from block specification."""
    b_id = block_def.get("id", "Block")
    b_name = block_def.get("name", "Section")
    func_name = block_def.get("func", sanitize_func_name(f"{b_id}_{b_name}"))
    elements = block_def.get("elements", block_def.get("shapes", []))

    lines = [
        f"# ==============================================================================",
        f"# {b_id.upper()}: {b_name}",
        f"# ==============================================================================",
        f"def {func_name}(builder: SlideBuilder) -> None:",
        f'    """Render {b_id}: {b_name} (100% Native Vector)."""',
    ]

    if not elements:
        box = block_def.get("box_norm", block_def.get("box", [50, 50, 900, 100]))
        lines.append(f"    # Default placeholder container")
        lines.append(f"    builder.add_card(box={box}, bg_color=\"#FFFFFF\", border_color=\"#E2E8F0\", radius=True)")
    else:
        for elem in elements:
            elem_lines = synth_element_code(elem, indent="    ")
            lines.extend(elem_lines)

    lines.append("")
    return "\n".join(lines)


def synth_full_slide_script(slide_name: str, blocks: List[Dict[str, Any]]) -> str:
    """Synthesize complete standalone executable Slide Builder Python script."""
    func_defs = []
    block_map_entries = []
    all_keys = []

    for idx, b in enumerate(blocks):
        b_id = b.get("id", f"Block {idx+1}")
        b_name = b.get("name", f"Section {idx+1}")
        func_name = b.get("func", sanitize_func_name(f"{b_id}_{b_name}"))
        b["func"] = func_name
        key_name = b_id.lower().replace(" ", "_")
        all_keys.append(key_name)

        func_defs.append(synth_block_function(b))
        block_map_entries.append(f'        "{key_name}": ("{b_id} [{b_name}]", {func_name}),')

    keys_str = ", ".join(f'"{k}"' for k in all_keys)

    template = f'''"""Modular Slide Construction Script: {slide_name} (100% Native Pure Vector Architecture)
Auto-synthesized by tools/synth_code.py.
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


{chr(10).join(func_defs)}

# ==============================================================================
# MAIN COMPOSER: build_{slide_name}
# ==============================================================================
def build_{slide_name}(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/{slide_name}.pptx",
) -> str:
    """Assemble slide from decoupled block modules with selective or cumulative build support."""
    print("=" * 60)
    print("🚀 Modular High-Fidelity Constructing Slide: {slide_name}")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")

    block_map = {{
{chr(10).join(block_map_entries)}
    }}

    all_keys = [{keys_str}]

    if cumulative_up_to is not None:
        if isinstance(cumulative_up_to, int) or (isinstance(cumulative_up_to, str) and str(cumulative_up_to).isdigit()):
            limit_idx = int(cumulative_up_to)
            target_blocks = all_keys[:limit_idx]
        elif str(cumulative_up_to).lower() in all_keys:
            limit_idx = all_keys.index(str(cumulative_up_to).lower()) + 1
            target_blocks = all_keys[:limit_idx]
        else:
            target_blocks = all_keys
    elif active_blocks is None:
        target_blocks = all_keys
    else:
        target_blocks = [b.lower() for b in active_blocks]

    for key in target_blocks:
        if key in block_map:
            name, func = block_map[key]
            print(f"  📦 Building {{name}}...")
            func(builder)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    builder.save(output_path)
    print(f"🎉 Successfully built Slide: {{output_path}}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Build {slide_name} with modular block architecture.")
    parser.add_argument("--blocks", nargs="+", default=None, help="Optional list of blocks to build")
    parser.add_argument("--cumulative-up-to", default=None, help="Build all blocks up to index (1-based) or key")
    parser.add_argument("-o", "--output", default="output/{slide_name}.pptx", help="Output .pptx path")
    args = parser.parse_args()

    build_{slide_name}(active_blocks=args.blocks, cumulative_up_to=args.cumulative_up_to, output_path=args.output)


if __name__ == "__main__":
    main()
'''
    return template


def main():
    parser = argparse.ArgumentParser(description="Synthesize Python Slide Builder Code from JSON Spec.")
    parser.add_argument("spec", help="Path to slide or block specification JSON file")
    parser.add_argument("-o", "--output", default=None, help="Output python file path")
    parser.add_argument("--slide-name", default="slide_auto", help="Name of slide module")
    args = parser.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        data = json.load(f)

    # If data is a list of elements (single block), wrap into blocks
    if isinstance(data, list):
        if data and "type" in data[0]:  # list of elements
            blocks = [{
                "id": "Block 1",
                "name": "Auto Synthesized Section",
                "elements": data
            }]
        else:  # list of blocks
            blocks = data
    elif isinstance(data, dict):
        blocks = data.get("blocks", [data])
    else:
        blocks = []

    code = synth_full_slide_script(args.slide_name, blocks)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[SynthCode] Python builder script synthesized: {args.output}")
    else:
        print(code)


if __name__ == "__main__":
    main()
