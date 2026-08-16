"""Slide 2 Modular Construction Script: 季度工作攻坚策略 (100% Native Block-by-Block Architecture)

Architecture:
- Block 1: `add_header_section(builder)` -> [35, 38, 930, 55] (Header & Author Tag)
- Block 2: `add_summary_banner_section(builder)` -> [35, 108, 930, 75] (Top Overview Banner)
- Block 3: `add_mid_kpi_section(builder)` -> [35, 192, 930, 110] (Efficiency Subtitle + 3 Composite KPI Cards)
- Block 4: `add_clipboard_table_section(builder)` -> [35, 325, 435, 600] (Layered Clipboard + Table + 5 Progress Bars)
- Block 5: `add_strategy_card_section(builder)` -> [485, 325, 480, 600] (2+1 Strategy Card + Action Cards + Footer Pills)
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


# ==============================================================================
# BLOCK 1: Header Section (主标题与作者标识)
# ==============================================================================
def add_header_section(builder: SlideBuilder) -> None:
    """Render Block 1: Main Title, Underline Divider Line, and Author Watermark."""
    # Main Title (GT measured: left=26, top=26, font_size=36pt, bold=True)
    builder.add_textbox(
        box=[26, 26, 600, 68],
        text="季度工作攻坚策略",
        font_size=36,
        font_color="#000000",
        bold=True,
    )
    # Underline Accent Divider Line (GT measured: left=26, top=96, width=948)
    builder.add_card(box=[26, 96, 948, 1.5], bg_color="#CBD5E1", border_color="transparent")
    # Right Author Tag (GT measured: right-aligned, font_size=20pt, bold=True)
    builder.add_textbox(
        box=[720, 35, 254, 55],
        text="@鱼丸PPT",
        font_size=20,
        font_color="#000000",
        bold=True,
        align="right",
    )


# ==============================================================================
# BLOCK 2: Top Summary Banner (总览概述胶囊横幅)
# ==============================================================================
def add_summary_banner_section(builder: SlideBuilder) -> None:
    """Render Block 2: Top Overview Summary Banner with Gradient Badge and Structured Runs."""
    # Outer Background Container (aligned with Block 1: left=26, width=948, top=112, height=72)
    builder.add_card(
        box=[26, 112, 948, 72],
        bg_color="#EBF4FC",
        border_color="#D1E4F7",
        border_width_pt=1.0,
        radius=True,
    )
    # Left Gradient Deep Blue Badge
    builder.add_card(
        box=[26, 112, 75, 72],
        gradient_colors=["#1D63B8", "#2575D0"],
        gradient_angle=135.0,
        border_color="transparent",
        radius=True,
    )
    builder.add_textbox(
        box=[26, 122, 75, 52],
        text="总览\n概述",
        font_size=14,
        font_color="#FFFFFF",
        bold=True,
        align="center",
    )
    # Right Rich Text Description (starts at left=112, width=848)
    builder.add_textbox(
        box=[112, 117, 850, 62],
        runs=[
            {"text": "本季度聚焦用户质量提升，核心指标达成率", "size": 11.5, "color": "#334155"},
            {"text": "89%", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "，同比增幅收窄至", "size": 11.5, "color": "#334155"},
            {"text": "3%", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "。通过重构活动投放策略，注册用户转化成本", "size": 11.5, "color": "#334155"},
            {"text": "降低21%", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "，但新客规模\n", "size": 11.5, "color": "#334155"},
            {"text": "缺口达12%", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "，付费转化率", "size": 11.5, "color": "#334155"},
            {"text": "6.1%（目标6.5%）", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "，运营成本", "size": 11.5, "color": "#334155"},
            {"text": "降幅9%（目标15%）", "size": 11.5, "bold": True, "color": "#0F172A"},
            {"text": "。", "size": 11.5, "color": "#334155"},
        ],
    )


# ==============================================================================
# BLOCK 3: Middle Subtitle & 3 Composite KPI Cards (多维度运营效能透视与指标卡)
# ==============================================================================
def add_mid_kpi_section(builder: SlideBuilder) -> None:
    """Render Block 3: Subtitle, Descriptive Summary, and 3 Stacked KPI Metric Cards with Flow Arrows."""
    # Left Subtitle & Text
    builder.add_textbox(
        box=[35, 205, 440, 30],
        text="多维度运营效能透视",
        font_size=18,
        font_color="#0F172A",
        bold=True,
    )
    builder.add_textbox(
        box=[35, 238, 440, 56],
        runs=[
            {"text": "推行精准获客策略后，高净值用户占比突破", "size": 10.5, "color": "#64748B"},
            {"text": "40%（+8pp）", "size": 10.5, "bold": True, "color": "#334155"},
            {"text": "，但新用户总量仅达成\n", "size": 10.5, "color": "#64748B"},
            {"text": "38万（目标45万）", "size": 10.5, "bold": True, "color": "#334155"},
            {"text": "。会员权益升级拉动复购率提升至", "size": 10.5, "color": "#64748B"},
            {"text": "19%（目标22%）", "size": 10.5, "bold": True, "color": "#334155"},
        ],
    )

    # --- KPI Card 1: 规模缺口 ---
    builder.add_card(
        box=[515, 192, 125, 105],
        bg_color="#F4F9FF",
        border_color="#BAE6FD",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_badge(
        box=[537, 180, 80, 24],
        text="规模缺口",
        bg_color="#FFFFFF",
        text_color="#0284C7",
        border_color="#60A5FA",
        border_width_pt=1.0,
        font_size=8.5,
        bold=True,
    )
    builder.add_textbox(
        box=[515, 212, 125, 42],
        text="38万",
        font_size=23,
        font_color="#0F172A",
        bold=True,
        align="center",
    )
    builder.add_badge(
        box=[532, 262, 90, 24],
        text="缺口16%",
        bg_color="#3B82F6",
        text_color="#FFFFFF",
        font_size=8.5,
        bold=True,
    )

    # Flow Arrow 1
    builder.add_badge(
        box=[652, 236, 22, 22],
        text="➔",
        gradient_colors=["#60A5FA", "#2563EB"],
        text_color="#FFFFFF",
        font_size=10,
        bold=True,
    )

    # --- KPI Card 2: 转化迟滞 ---
    builder.add_card(
        box=[685, 192, 125, 105],
        bg_color="#F4F9FF",
        border_color="#BAE6FD",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_badge(
        box=[707, 180, 80, 24],
        text="转化迟滞",
        bg_color="#FFFFFF",
        text_color="#0284C7",
        border_color="#60A5FA",
        border_width_pt=1.0,
        font_size=8.5,
        bold=True,
    )
    builder.add_textbox(
        box=[685, 212, 125, 42],
        text="6.1%",
        font_size=23,
        font_color="#0F172A",
        bold=True,
        align="center",
    )
    builder.add_badge(
        box=[702, 262, 90, 24],
        text="缺口0.4pp",
        bg_color="#3B82F6",
        text_color="#FFFFFF",
        font_size=8.5,
        bold=True,
    )

    # Flow Arrow 2
    builder.add_badge(
        box=[822, 236, 22, 22],
        text="➔",
        gradient_colors=["#F87171", "#DC2626"],
        text_color="#FFFFFF",
        font_size=10,
        bold=True,
    )

    # --- KPI Card 3: 成本刚性 ---
    builder.add_card(
        box=[852, 192, 120, 105],
        bg_color="#FEF5F5",
        border_color="#FECACA",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_badge(
        box=[872, 180, 80, 24],
        text="成本刚性",
        bg_color="#FFFFFF",
        text_color="#DC2626",
        border_color="#F87171",
        border_width_pt=1.0,
        font_size=8.5,
        bold=True,
    )
    builder.add_textbox(
        box=[852, 212, 120, 42],
        text="9%降幅",
        font_size=21,
        font_color="#0F172A",
        bold=True,
        align="center",
    )
    builder.add_badge(
        box=[867, 262, 90, 24],
        text="缺口6pp",
        bg_color="#DC2626",
        text_color="#FFFFFF",
        font_size=8.5,
        bold=True,
    )


# ==============================================================================
# BLOCK 4: Bottom Left Layered Clipboard (拟物板夹 + 表格 + 发光进度条)
# ==============================================================================
def add_clipboard_table_section(builder: SlideBuilder) -> None:
    """Render Block 4: Layered Clipboard Container, Native Data Table, and 5 Glowing Progress Bars."""
    # 1. Clipboard Baseplate (Gradient Royal Blue with Subtle Rounded Corners)
    builder.add_card(
        box=[35, 308, 438, 640],
        gradient_colors=["#1E5AA0", "#2B78C9"],
        gradient_angle=135.0,
        border_color="#154A85",
        border_width_pt=1.5,
        radius=True,
    )

    # Top Metallic Clip Accent (3-Layer Photorealistic Clip)
    # Layer 1: Dark Slate Base Plate
    builder.add_card(
        box=[205, 295, 95, 20],
        bg_color="#64748B",
        border_color="#475569",
        border_width_pt=1.0,
        radius=True,
    )
    # Layer 2: Metallic Silver Plate
    builder.add_card(
        box=[212, 299, 81, 14],
        bg_color="#E2E8F0",
        border_color="#94A3B8",
        border_width_pt=0.8,
        radius=True,
    )
    # Layer 3: Inner Hanging Slot Hole
    builder.add_card(
        box=[238, 303, 29, 6],
        bg_color="#475569",
        border_color="transparent",
        radius=True,
    )

    # 2. Inner White Paper Sheet
    builder.add_card(
        box=[44, 318, 420, 620],
        bg_color="#FFFFFF",
        border_color="#CBD5E1",
        border_width_pt=1.0,
        radius=True,
    )

    # Paper Title: 核心战役完成度全景 (Strictly Centered, 20pt Heavy Bold at y: 336)
    builder.add_textbox(
        box=[44, 336, 420, 36],
        text="核心战役完成度全景",
        font_size=20,
        font_color="#0F172A",
        bold=True,
        align="center",
    )

    # 3. Glossy Table Header Bar (Vibrant Linear Gradient at y: 378)
    builder.add_card(
        box=[52, 378, 404, 38],
        gradient_colors=["#428BD6", "#165096"],
        gradient_angle=90.0,
        radius=True,
        border_color="#18529C",
        border_width_pt=0.8,
    )
    # Header Column Titles (Crisp 12pt Bold White Text)
    # Col 1: Left-aligned with 14px margin
    builder.add_textbox(box=[66, 383, 80, 28], text="项目名称", font_size=12, font_color="#FFFFFF", bold=True, align="left")
    # Col 2 & 3: Centered
    builder.add_textbox(box=[146, 383, 52, 28], text="目标值", font_size=12, font_color="#FFFFFF", bold=True, align="center")
    builder.add_textbox(box=[198, 383, 52, 28], text="实际值", font_size=12, font_color="#FFFFFF", bold=True, align="center")
    # Col 4: Centered over progress bars
    builder.add_textbox(box=[250, 383, 206, 28], text="整体完成率", font_size=12, font_color="#FFFFFF", bold=True, align="center")

    # 4. Zebra Row 2 & Row 4 Background Cards (Soft Peach with Rounded Corners)
    builder.add_card(box=[52, 490, 404, 60], bg_color="#FEF2F0", border_color="transparent", radius=True)
    builder.add_card(box=[52, 626, 404, 60], bg_color="#FEF2F0", border_color="transparent", radius=True)

    # 5. 5 Data Rows: Labels (Left Aligned), Targets (Centered), Actuals (Centered), and Progress Bars
    rows_data = [
        ("新用户招募", "45万", "38万", 0.84, "84%", 426),
        ("用户留存率", "70%", "69%", 0.99, "99%", 494),
        ("活动ROI", "1:5", "1:4:2", 0.84, "84%", 562),
        ("响应时效", "2.5h", "2.1h", 0.82, "82%", 630),
        ("用户调研量", "2500", "1620", 0.65, "65%", 698),
    ]

    for name_lbl, target_lbl, actual_lbl, pct_val, text_pct, y_start in rows_data:
        # Col 1: Name (Strictly LEFT-ALIGNED at x: 66, matching Header)
        builder.add_textbox(box=[66, y_start + 8, 80, 30], text=name_lbl, font_size=12, font_color="#334155", align="left")
        # Col 2: Target (Centered at x: 146)
        builder.add_textbox(box=[146, y_start + 8, 52, 30], text=target_lbl, font_size=12, font_color="#334155", align="center")
        # Col 3: Actual (Centered at x: 198)
        builder.add_textbox(box=[198, y_start + 8, 52, 30], text=actual_lbl, font_size=12, font_color="#334155", align="center")
        # Col 4: Progress Bar + Percent Label
        builder.add_progress_bar(
            box=[252, y_start + 15, 148, 16],
            pct=pct_val,
            text=text_pct,
            bar_color="#C2410C",
            gradient_colors=["#8B2515", "#C2410C"],
            gradient_angle=90.0,
            bg_color="#FCE6DC",
            node_glow=True,
            font_size=11,
            text_color="#9A3412",
        )


# ==============================================================================
# BLOCK 5: Bottom Right Strategy Card (2+1 破局行动战略大卡 - 100% 还原原图)
# ==============================================================================
def add_strategy_card_section(builder: SlideBuilder) -> None:
    """Render Block 5: 2+1 Strategy Card with separate title strips on white card surface."""
    # 1. Outer Container Card (Pure White card with subtle blue border)
    builder.add_card(
        box=[480, 318, 494, 602],
        bg_color="#FFFFFF",
        border_color="#BAE6FD",
        border_width_pt=1.2,
        radius=True,
    )

    # 2. Top Blue Gradient Header Bar (Horizontal Gradient: #2167BA -> #589CE3)
    builder.add_card(
        box=[480, 318, 494, 82],
        gradient_colors=["#2167BA", "#589CE3"],
        gradient_angle=0.0,
        border_color="transparent",
        radius=True,
    )

    # Strategy Title: "2+1" (Huge Bold White 42pt) + "破局行动" (Bold White 23pt)
    builder.add_textbox(box=[492, 322, 88, 76], text="2+1", font_size=42, font_color="#FFFFFF", bold=True)
    builder.add_textbox(box=[580, 336, 120, 52], text="破局行动", font_size=23, font_color="#FFFFFF", bold=True)
    
    # Right Quote Pill Badge
    builder.add_badge(
        box=[705, 340, 256, 38],
        text="“在裂缝中寻找光，向结构要效率！”",
        bg_color="#143E75",
        text_color="#FFFFFF",
        font_size=10,
        bold=True,
    )

    # 3. Action Section 1
    # 3.1 仅标题行有淡蓝条形底板 (Title Strip)
    builder.add_card(
        box=[488, 412, 474, 38],
        bg_color="#EDF6FD",
        border_color="transparent",
        radius=True,
    )
    builder.add_badge(
        box=[494, 416, 30, 30],
        text="1",
        bg_color="#1456AA",
        text_color="#FFFFFF",
        font_size=13,
        bold=True,
    )
    builder.add_textbox(
        box=[532, 416, 425, 30],
        text="流量重构-突破渠道瓶颈",
        font_size=15,
        font_color="#0F172A",
        bold=True,
    )
    # 3.2 正文子弹项 (直接排在纯白底板上，无底卡包裹)
    builder.add_textbox(box=[500, 456, 600, 22], text="• 阶梯式缩量: 对低效渠道实施每周10%的预算递减机制", font_size=10.5, font_color="#334155", word_wrap=False)
    builder.add_textbox(box=[500, 482, 600, 22], text="• 建立新渠道试投池: 定向开发KOC种草、垂直社区等新型渠道，首批测试ROI达1:4.5", font_size=10.5, font_color="#334155", word_wrap=False)

    # 4. Action Section 2
    # 4.1 仅标题行有淡蓝条形底板 (Title Strip)
    builder.add_card(
        box=[488, 518, 474, 38],
        bg_color="#EDF6FD",
        border_color="transparent",
        radius=True,
    )
    builder.add_badge(
        box=[494, 522, 30, 30],
        text="2",
        bg_color="#1456AA",
        text_color="#FFFFFF",
        font_size=13,
        bold=True,
    )
    builder.add_textbox(
        box=[532, 522, 425, 30],
        text="触点再造 - 激活沉默资产",
        font_size=15,
        font_color="#0F172A",
        bold=True,
    )
    # 4.2 正文子弹项 (直接排在纯白底板上，无底卡包裹)
    builder.add_textbox(box=[500, 562, 600, 22], text="• 黄金72小时: 对高价值用户推送专属权益包（含¥50无门槛券+会员体验）", font_size=10.5, font_color="#334155", word_wrap=False)
    builder.add_textbox(box=[500, 588, 600, 22], text="• 周期性刺激: 对中频用户每月推送品类专属优惠（美妆/母婴等定向满减）", font_size=10.5, font_color="#334155", word_wrap=False)


    # 5. Bottom Footer Container Bar
    builder.add_card(
        box=[480, 842, 494, 68],
        bg_color="#EBF4FC",
        border_color="transparent",
        radius=True,
    )

    # 6. Bottom Strategy Keyword Badges (Balanced distribution across 470px span)
    builder.add_badge(
        box=[492, 856, 146, 38],
        text="在存量战场挖掘增量价值",
        bg_color="#1D63B8",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )
    pills = ["渠道洗牌", "沉默唤醒", "成本攻坚", "精准刀法"]
    for i, p_txt in enumerate(pills):
        builder.add_badge(
            box=[648 + i * 82, 856, 72, 38],
            text=p_txt,
            bg_color="#FFFFFF",
            border_color="#93C5FD",
            text_color="#1E40AF",
            font_size=9.5,
            bold=True,
        )


# ==============================================================================
# MAIN COMPOSER: build_slide_02 (Modular Assembly & Isolated Block Debugging)
# ==============================================================================
def build_slide_02(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/slide_02.pptx",
) -> str:
    """Assemble slide from decoupled block modules or render selected/cumulative blocks."""
    print("=" * 60)
    print("🚀 Modular High-Fidelity Constructing Slide 02: 季度工作攻坚策略")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#FFFFFF")

    block_map = {
        "header": ("Block 1 [Header]", add_header_section),
        "summary": ("Block 2 [Summary Banner]", add_summary_banner_section),
        "kpi": ("Block 3 [Middle Subtitle & KPI Cards]", add_mid_kpi_section),
        "clipboard": ("Block 4 [Left Clipboard Table]", add_clipboard_table_section),
        "strategy": ("Block 5 [Right Strategy Card]", add_strategy_card_section),
    }

    all_keys = ["header", "summary", "kpi", "clipboard", "strategy"]

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

    builder.save(output_path)
    print(f"🎉 Successfully built Slide 02: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Build Slide 02 with modular block architecture.")
    parser.add_argument(
        "--blocks",
        nargs="+",
        default=None,
        help="Optional list of blocks to build (header, summary, kpi, clipboard, strategy)",
    )
    parser.add_argument(
        "--cumulative-up-to",
        default=None,
        help="Build all blocks up to index (1-based, e.g. 2) or key (e.g. summary)",
    )
    parser.add_argument("-o", "--output", default="output/slide_02.pptx", help="Output .pptx path")
    args = parser.parse_args()

    build_slide_02(active_blocks=args.blocks, cumulative_up_to=args.cumulative_up_to, output_path=args.output)


if __name__ == "__main__":
    main()
