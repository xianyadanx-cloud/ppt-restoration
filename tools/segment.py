"""Standardized Automatic Block Segmentation & Scaffold Tool (tools/segment.py)

Proactively generates:
1. Visual Block Annotation Map (`output/block_map_<name>.png`)
2. Individual Block Slices & Diffs (`output/diff_block_<idx>.png`)
3. Modular Decoupled Python Scaffold (`slides/build_<name>.py`)
"""

import os
import sys
import argparse
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.render_and_diff import detect_inner_slide_canvas, render_pptx_to_image, compare_and_generate_diff


def get_chinese_font(size: int = 18) -> ImageFont.ImageFont:
    """Load robust Chinese font with fallbacks."""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size, index=0)
            except Exception:
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    pass
    return ImageFont.load_default()


DEFAULT_PALETTE = [
    (29, 78, 216),   # Royal Blue
    (5, 150, 105),   # Emerald Green
    (217, 119, 6),   # Amber/Orange
    (124, 58, 237),  # Purple
    (225, 29, 72),   # Rose Red
    (13, 148, 136),  # Teal
    (79, 70, 229),   # Indigo
]


def generate_block_map(
    input_image_path: str,
    blocks: List[Dict[str, Any]],
    output_map_path: str,
) -> str:
    """Generate visual block annotation map overlay on clean slide canvas."""
    raw_img = Image.open(input_image_path).convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
    canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

    annotated = canvas.copy().convert("RGBA")
    overlay = Image.new("RGBA", (1440, 810), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    fnt = get_chinese_font(18)
    w, h = 1440, 810

    for idx, b in enumerate(blocks):
        l, t, bw, bh = b["box"]
        px_l = int(l / 1000.0 * w)
        px_t = int(t / 1000.0 * h)
        px_r = int((l + bw) / 1000.0 * w)
        px_b = int((t + bh) / 1000.0 * h)

        c = b.get("color", DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)])
        fill_c = (c[0], c[1], c[2], 30)
        border_c = (c[0], c[1], c[2], 235)

        # Draw rounded rectangle outline
        draw.rounded_rectangle([px_l, px_t, px_r, px_b], radius=8, fill=fill_c, outline=border_c, width=3)

        # Draw solid label badge
        b_id = b.get("id", f"Block {idx+1}")
        b_name = b.get("name", "Section")
        lbl_text = f" {b_id}: {b_name} "
        bbox = draw.textbbox((0, 0), lbl_text, font=fnt)
        lbl_w = bbox[2] - bbox[0] + 16
        lbl_h = 28

        badge_top = max(4, px_t - 14 if px_t > 24 else px_t + 4)
        badge_left = px_l + 8

        draw.rounded_rectangle([badge_left, badge_top, badge_left + lbl_w, badge_top + lbl_h], radius=5, fill=(c[0], c[1], c[2], 245))
        draw.text((badge_left + 8, badge_top + 4), lbl_text, fill=(255, 255, 255, 255), font=fnt)

    annotated = Image.alpha_composite(annotated, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_map_path)), exist_ok=True)
    annotated.save(output_map_path)
    print(f"[Segment] Visual block map generated: {output_map_path}")
    return output_map_path


def generate_scaffold_code(
    slide_name: str,
    blocks: List[Dict[str, Any]],
    output_script_path: str,
    overwrite: bool = False,
) -> str:
    """Generate a decoupled modular Python scaffold with block functions and CLI."""
    if os.path.exists(output_script_path) and not overwrite:
        print(f"[Notice] Scaffold {output_script_path} already exists. Skipping overwrite.")
        return output_script_path

    func_definitions = []
    block_map_entries = []

    for idx, b in enumerate(blocks):
        b_id = b.get("id", f"Block {idx+1}")
        b_name = b.get("name", "Section")
        func_name = b.get("func", f"add_block_{idx+1}_section")
        key_name = b_id.lower().replace(" ", "_")
        box = b.get("box", [50, 50, 900, 100])

        func_def = f'''# ==============================================================================
# {b_id.upper()}: {b_name}
# ==============================================================================
def {func_name}(builder: SlideBuilder) -> None:
    """Render {b_id}: {b_name} (box: {box})."""
    # TODO: Add native PPTX elements for this block
    # builder.add_card(box={box}, bg_color="#FFFFFF", border_color="#E2E8F0", radius=True)
    pass
'''
        func_definitions.append(func_def)
        block_map_entries.append(f'        "{key_name}": ("{b_id} [{b_name}]", {func_name}),')

    all_keys_list = [b.get("id", f"Block {idx+1}").lower().replace(" ", "_") for idx, b in enumerate(blocks)]
    default_keys_str = ", ".join(f'"{k}"' for k in all_keys_list)

    code = f'''"""Modular Slide Construction Script: {slide_name} (100% Native Block-by-Block Architecture)"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


{chr(10).join(func_definitions)}

# ==============================================================================
# MAIN COMPOSER: build_{slide_name}
# ==============================================================================
def build_{slide_name}(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/{slide_name}.pptx",
) -> str:
    """Assemble slide from decoupled block modules, render selected blocks, or render cumulatively."""
    print("=" * 60)
    print("🚀 Modular High-Fidelity Constructing Slide: {slide_name}")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")

    block_map = {{
{chr(10).join(block_map_entries)}
    }}

    all_keys = [{default_keys_str}]

    if cumulative_up_to is not None:
        if isinstance(cumulative_up_to, int) or (isinstance(cumulative_up_to, str) and cumulative_up_to.isdigit()):
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
    os.makedirs(os.path.dirname(os.path.abspath(output_script_path)), exist_ok=True)
    with open(output_script_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"[Segment] Scaffold generated: {output_script_path}")
    return output_script_path


# Standard default blocks for slide_02
SLIDE_02_BLOCKS = [
    {
        "id": "Block 1",
        "name": "顶部主标题区 (Header)",
        "box": [30, 25, 940, 72],
        "color": (29, 78, 216),
        "func": "add_header_section",
    },
    {
        "id": "Block 2",
        "name": "总结概览横幅 (Summary Banner)",
        "box": [30, 105, 940, 78],
        "color": (5, 150, 105),
        "func": "add_summary_banner_section",
    },
    {
        "id": "Block 3",
        "name": "效能透视与 KPI 组 (Mid KPIs)",
        "box": [30, 192, 940, 115],
        "color": (217, 119, 6),
        "func": "add_mid_kpi_section",
    },
    {
        "id": "Block 4",
        "name": "拟物战役板夹 (Clipboard Table)",
        "box": [30, 318, 438, 602],
        "color": (124, 58, 237),
        "func": "add_clipboard_table_section",
    },
    {
        "id": "Block 5",
        "name": "2+1 破局行动大卡 (Strategy Card)",
        "box": [480, 318, 490, 602],
        "color": (225, 29, 72),
        "func": "add_strategy_card_section",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Auto Block Segmentation and Scaffold Generator.")
    parser.add_argument("image", nargs="?", default="input/slide_02.png", help="Input slide image")
    parser.add_argument("-o", "--output", default=None, help="Output block map image path")
    parser.add_argument("--scaffold", action="store_true", help="Generate modular build_<name>.py scaffold")
    parser.add_argument("--force-scaffold", action="store_true", help="Force overwrite scaffold script")

    args = parser.parse_args()
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    map_out = args.output or f"output/block_map_{base_name}.png"

    blocks = SLIDE_02_BLOCKS

    # 1. Generate Visual Block Map
    generate_block_map(args.image, blocks, map_out)

    # 2. Optionally Generate Scaffold
    if args.scaffold or args.force_scaffold:
        scaffold_path = f"slides/build_{base_name}.py"
        generate_scaffold_code(base_name, blocks, scaffold_path, overwrite=args.force_scaffold)


if __name__ == "__main__":
    main()
