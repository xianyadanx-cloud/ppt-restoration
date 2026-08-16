"""Modular Slide Construction Script: slide_02_synth (100% Native Pure Vector Architecture)
Auto-synthesized by tools/synth_code.py.
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


# ==============================================================================
# BLOCK 1: Auto Synthesized Section
# ==============================================================================
def add_Block_1_Auto_Synthesized_Section_section(builder: SlideBuilder) -> None:
    """Render Block 1: Auto Synthesized Section (100% Native Vector)."""
    # --- 外层白底容器卡 (solid_card) ---
    builder.add_card(
        box=[480, 318, 494, 602],
        bg_color="#FFFFFF",
        radius=True,
    )
    # --- 顶部横幅渐变 (gradient_card) ---
    builder.add_card(
        box=[484, 322, 486, 74],
        gradient_colors=['#2563EB', '#60A5FA'],
        gradient_angle=90.0,
        border_color="transparent",
        radius=True,
    )
    # --- 行动区域统一底卡 (solid_card) ---
    builder.add_card(
        box=[488, 404, 474, 308],
        bg_color="#FFFFFF",
        radius=True,
    )
    # --- 行动1徽章 (badge) ---
    builder.add_badge(
        box=[496, 413, 30, 30],
        text="",
        bg_color="#2563EB",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )
    # --- 行动2徽章 (badge) ---
    builder.add_badge(
        box=[496, 518, 30, 30],
        text="",
        bg_color="#2563EB",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )
    # --- 底部Footer栏 (solid_card) ---
    builder.add_card(
        box=[480, 842, 494, 68],
        bg_color="#FFFFFF",
        radius=True,
    )
    # --- 蓝色实心胶囊 (badge) ---
    builder.add_badge(
        box=[492, 856, 146, 38],
        text="",
        bg_color="#2563EB",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )
    # --- 行动1标题文字 (text) ---
    builder.add_textbox(
        box=[534, 413, 400, 32],
        text="",
        font_size=14,
        font_color="#0F172A",
        bold=False,
    )


# ==============================================================================
# MAIN COMPOSER: build_slide_02_synth
# ==============================================================================
def build_slide_02_synth(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/slide_02_synth.pptx",
) -> str:
    """Assemble slide from decoupled block modules with selective or cumulative build support."""
    print("=" * 60)
    print("🚀 Modular High-Fidelity Constructing Slide: slide_02_synth")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")

    block_map = {
        "block_1": ("Block 1 [Auto Synthesized Section]", add_Block_1_Auto_Synthesized_Section_section),
    }

    all_keys = ["block_1"]

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
            print(f"  📦 Building {name}...")
            func(builder)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    builder.save(output_path)
    print(f"🎉 Successfully built Slide: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Build slide_02_synth with modular block architecture.")
    parser.add_argument("--blocks", nargs="+", default=None, help="Optional list of blocks to build")
    parser.add_argument("--cumulative-up-to", default=None, help="Build all blocks up to index (1-based) or key")
    parser.add_argument("-o", "--output", default="output/slide_02_synth.pptx", help="Output .pptx path")
    args = parser.parse_args()

    build_slide_02_synth(active_blocks=args.blocks, cumulative_up_to=args.cumulative_up_to, output_path=args.output)


if __name__ == "__main__":
    main()
