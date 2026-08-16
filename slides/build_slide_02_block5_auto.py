"""Modular Slide Construction Script: slide_02_block5_auto (100% Native Pure Vector Architecture)
Auto-synthesized by tools/synth_code.py.
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


# ==============================================================================
# BLOCK 5: 2+1 破局行动战略大卡 (Strategy Card)
# ==============================================================================
def add_strategy_card_section(builder: SlideBuilder) -> None:
    """Render Block 5: 2+1 破局行动战略大卡 (Strategy Card) (100% Native Vector)."""
    # --- 外层白底容器大卡 (card) ---
    builder.add_card(
        box=[480, 318, 494, 602],
        bg_color="#FFFFFF",
        border_color="#BAE6FD",
        border_width_pt=1.2,
        radius=True,
    )
    # --- 顶部水平渐变横幅 (gradient_card) ---
    builder.add_card(
        box=[480, 318, 494, 82],
        gradient_colors=['#2167BA', '#589CE3'],
        gradient_angle=0.0,
        border_color="transparent",
        radius=True,
    )
    # --- 主标 2+1 (text) ---
    builder.add_textbox(
        box=[492, 322, 88, 76],
        text="2+1",
        font_size=42,
        font_color="#FFFFFF",
        bold=True,
    )
    # --- 副标 破局行动 (text) ---
    builder.add_textbox(
        box=[580, 336, 120, 52],
        text="破局行动",
        font_size=23,
        font_color="#FFFFFF",
        bold=True,
    )
    # --- 右侧金句深蓝胶囊 (badge) ---
    builder.add_badge(
        box=[705, 340, 256, 38],
        text="“在裂缝中寻找光，向结构要效率！”",
        bg_color="#143E75",
        text_color="#FFFFFF",
        font_size=10,
        bold=True,
    )
    # --- 行动区域统一淡蓝底卡 (card) ---
    builder.add_card(
        box=[488, 404, 474, 308],
        bg_color="#EBF5FC",
        border_color="#93C5FD",
        border_width_pt=1.0,
        radius=True,
    )
    # --- 行动1序号徽章 (badge) ---
    builder.add_badge(
        box=[496, 413, 30, 30],
        text="1",
        bg_color="#1456AA",
        text_color="#FFFFFF",
        font_size=13,
        bold=True,
    )
    # --- 行动1标题 (text) ---
    builder.add_textbox(
        box=[534, 413, 425, 32],
        text="流量重构-突破渠道瓶颈",
        font_size=15,
        font_color="#0F172A",
        bold=True,
    )
    # --- 行动1子弹项1 (text) ---
    builder.add_textbox(
        box=[500, 450, 600, 22],
        text="• 阶梯式缩量: 对低效渠道实施每周10%的预算递减机制",
        font_size=10.5,
        font_color="#334155",
        bold=False,
        word_wrap=False,
    )
    # --- 行动1子弹项2 (text) ---
    builder.add_textbox(
        box=[500, 476, 600, 22],
        text="• 建立新渠道试投池: 定向开发KOC种草、垂直社区等新型渠道，首批测试ROI达1:4.5",
        font_size=10.5,
        font_color="#334155",
        bold=False,
        word_wrap=False,
    )
    # --- 行动区分割线 (card) ---
    builder.add_card(
        box=[496, 510, 458, 2],
        bg_color="#CBD5E1",
        radius=False,
    )
    # --- 行动2序号徽章 (badge) ---
    builder.add_badge(
        box=[496, 518, 30, 30],
        text="2",
        bg_color="#1456AA",
        text_color="#FFFFFF",
        font_size=13,
        bold=True,
    )
    # --- 行动2标题 (text) ---
    builder.add_textbox(
        box=[534, 518, 425, 32],
        text="触点再造 - 激活沉默资产",
        font_size=15,
        font_color="#0F172A",
        bold=True,
    )
    # --- 行动2子弹项1 (text) ---
    builder.add_textbox(
        box=[500, 558, 600, 22],
        text="• 黄金72小时: 对高价值用户推送专属权益包（含¥50无门槛券+会员体验）",
        font_size=10.5,
        font_color="#334155",
        bold=False,
        word_wrap=False,
    )
    # --- 行动2子弹项2 (text) ---
    builder.add_textbox(
        box=[500, 584, 600, 22],
        text="• 周期性刺激: 对中频用户每月推送品类专属优惠（美妆/母婴等定向满减）",
        font_size=10.5,
        font_color="#334155",
        bold=False,
        word_wrap=False,
    )
    # --- 底部Footer底栏 (card) ---
    builder.add_card(
        box=[480, 842, 494, 68],
        bg_color="#EBF4FC",
        radius=True,
    )
    # --- 底部蓝色实心主胶囊 (badge) ---
    builder.add_badge(
        box=[492, 856, 146, 38],
        text="在存量战场挖掘增量价值",
        bg_color="#1D63B8",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )
    # --- 底部关键词药丸1 渠道洗牌 (badge) ---
    builder.add_badge(
        box=[648, 856, 72, 38],
        text="渠道洗牌",
        bg_color="#FFFFFF",
        border_color="#93C5FD",
        text_color="#1E40AF",
        font_size=9.5,
        bold=True,
    )
    # --- 底部关键词药丸2 沉默唤醒 (badge) ---
    builder.add_badge(
        box=[730, 856, 72, 38],
        text="沉默唤醒",
        bg_color="#FFFFFF",
        border_color="#93C5FD",
        text_color="#1E40AF",
        font_size=9.5,
        bold=True,
    )
    # --- 底部关键词药丸3 成本攻坚 (badge) ---
    builder.add_badge(
        box=[812, 856, 72, 38],
        text="成本攻坚",
        bg_color="#FFFFFF",
        border_color="#93C5FD",
        text_color="#1E40AF",
        font_size=9.5,
        bold=True,
    )
    # --- 底部关键词药丸4 精准刀法 (badge) ---
    builder.add_badge(
        box=[894, 856, 72, 38],
        text="精准刀法",
        bg_color="#FFFFFF",
        border_color="#93C5FD",
        text_color="#1E40AF",
        font_size=9.5,
        bold=True,
    )


# ==============================================================================
# MAIN COMPOSER: build_slide_02_block5_auto
# ==============================================================================
def build_slide_02_block5_auto(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/slide_02_block5_auto.pptx",
) -> str:
    """Assemble slide from decoupled block modules with selective or cumulative build support."""
    print("=" * 60)
    print("🚀 Modular High-Fidelity Constructing Slide: slide_02_block5_auto")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")

    block_map = {
        "block_5": ("Block 5 [2+1 破局行动战略大卡 (Strategy Card)]", add_strategy_card_section),
    }

    all_keys = ["block_5"]

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
    parser = argparse.ArgumentParser(description="Build slide_02_block5_auto with modular block architecture.")
    parser.add_argument("--blocks", nargs="+", default=None, help="Optional list of blocks to build")
    parser.add_argument("--cumulative-up-to", default=None, help="Build all blocks up to index (1-based) or key")
    parser.add_argument("-o", "--output", default="output/slide_02_block5_auto.pptx", help="Output .pptx path")
    args = parser.parse_args()

    build_slide_02_block5_auto(active_blocks=args.blocks, cumulative_up_to=args.cumulative_up_to, output_path=args.output)


if __name__ == "__main__":
    main()
