"""Slide 2 Modular Construction Script: 季度工作攻坚策略 (100% Native Block-by-Block Architecture)

Architecture:
- Block 1: `add_header_section(builder)` -> [26, 28, 948, 60] (Header & Author Tag)
- Block 2: `add_summary_banner_section(builder)` -> [26, 104, 948, 64] (Top Overview Banner)
- Block 3: `add_mid_kpi_section(builder)` -> [32, 198, 938, 96] (Efficiency Subtitle + 3 Composite KPI Cards)
- Block 4: `add_clipboard_table_section(builder)` -> [32, 315, 438, 605] (Layered Clipboard + Table + 5 Progress Bars)
- Block 5: `add_strategy_card_section(builder)` -> [486, 315, 484, 605] (2+1 Strategy Card + Action Cards + Footer Pills)
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder, Tokens


# ==============================================================================
# BLOCK 1: Header Section (主标题与作者标识)
# ==============================================================================
def add_header_section(builder: SlideBuilder) -> None:
    """Render Block 1: Main Title, Underline Divider Line, and Author Watermark."""
    # Main Title (GT measured: left=26, top=28, font_size=28pt Bold)
    builder.add_textbox(
        box=[26, 28, 600, 52],
        text="季度工作攻坚策略",
        font_size=28,
        auto_fit_font=True,
        font_color="#000000",
        bold=True,
    )
    # Underline Accent Divider Line (GT measured: left=26, top=88, width=948, 0.75pt)
    builder.add_card(box=[26, 88, 948, 1.0], bg_color="#CBD5E1", border_color="transparent")
    # Right Author Tag (GT measured: right-aligned, font_size=14pt Bold)
    builder.add_textbox(
        box=[720, 38, 254, 40],
        text="@鱼丸PPT",
        font_size=14,
        auto_fit_font=True,
        font_color="#000000",
        bold=True,
        align="right",
    )


# ==============================================================================
# BLOCK 2: Top Summary Banner (总览概述胶囊横幅)
# ==============================================================================
def add_summary_banner_section(builder: SlideBuilder) -> None:
    """Render Block 2: Top Overview Summary Banner with Gradient Badge and Structured Runs."""
    # Outer Background Container (aligned with Block 1: left=26, width=948, top=104, height=64)
    builder.add_card(
        box=[26, 104, 948, 64],
        bg_color="#EBF4FC",
        border_color="#D1E4F7",
        border_width_pt=1.0,
        radius=True,
    )
    # Left Gradient Deep Blue Badge
    builder.add_card(
        box=[26, 104, 70, 64],
        gradient_colors=["#1D63B8", "#2575D0"],
        gradient_angle=135.0,
        border_color="transparent",
        radius=True,
    )
    builder.add_textbox(
        box=[26, 114, 70, 44],
        text="总览\n概述",
        font_size=13,
        font_color="#FFFFFF",
        bold=True,
        align="center",
    )
    # Right Rich Text Description
    builder.add_textbox(
        box=[106, 108, 856, 56],
        runs=[
            {"text": "本季度聚焦用户质量提升，核心指标达成率", "size": 11.0, "color": "#334155"},
            {"text": "89%", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "，同比增幅收窄至", "size": 11.0, "color": "#334155"},
            {"text": "3%", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "。通过重构活动投放策略，注册用户转化成本", "size": 11.0, "color": "#334155"},
            {"text": "降低21%", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "，但新客规模\n", "size": 11.0, "color": "#334155"},
            {"text": "缺口达12%", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "，付费转化率", "size": 11.0, "color": "#334155"},
            {"text": "6.1%（目标6.5%）", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "，运营成本", "size": 11.0, "color": "#334155"},
            {"text": "降幅9%（目标15%）", "size": 11.0, "bold": True, "color": "#0F172A"},
            {"text": "。", "size": 11.0, "color": "#334155"},
        ],
    )


# ==============================================================================
# BLOCK 3: Middle Subtitle & 3 Composite KPI Cards (多维度运营效能透视与指标卡)
# ==============================================================================
def add_mid_kpi_section(builder: SlideBuilder) -> None:
    """Render Block 3: Subtitle, Descriptive Summary, and 3 Stacked KPI Metric Cards with Flow Arrows."""
    # Left Subtitle & Text (top: 198)
    builder.add_textbox(
        box=[32, 198, 440, 28],
        text="多维度运营效能透视",
        font_size=16,
        font_color="#0F172A",
        bold=True,
    )
    builder.add_textbox(
        box=[32, 228, 440, 52],
        runs=[
            {"text": "推行精准获客策略后，高净值用户占比突破", "size": 10.0, "color": "#64748B"},
            {"text": "40%（+8pp）", "size": 10.0, "bold": True, "color": "#334155"},
            {"text": "，但新用户总量仅达成\n", "size": 10.0, "color": "#64748B"},
            {"text": "38万（目标45万）", "size": 10.0, "bold": True, "color": "#334155"},
            {"text": "。会员权益升级拉动复购率提升至", "size": 10.0, "color": "#64748B"},
            {"text": "19%（目标22%）", "size": 10.0, "bold": True, "color": "#334155"},
        ],
    )

    # Right 3 columns grid for KPI cards (top: 198, height: 96, gap_x: 32)
    grid_boxes = builder.add_grid(box=[505, 198, 465, 96], cols=3, rows=1, gap_x=32)

    # KPI 1
    builder.add_kpi_card(
        box=grid_boxes[0],
        top_tag="规模缺口",
        value="38万",
        bottom_badge="缺口16%",
        theme_color="#0284C7",
        bg_color="#F4F9FF",
        border_color="#BAE6FD",
        tag_bg="#FFFFFF"
    )
    # Arrow 1
    builder.add_badge(
        box=[644, 235, 20, 20],
        text="➔",
        gradient_colors=["#60A5FA", "#2563EB"],
        text_color="#FFFFFF",
        font_size=9,
        bold=True,
    )

    # KPI 2
    builder.add_kpi_card(
        box=grid_boxes[1],
        top_tag="转化迟滞",
        value="6.1%",
        bottom_badge="缺口0.4pp",
        theme_color="#0284C7",
        bg_color="#F4F9FF",
        border_color="#BAE6FD",
        tag_bg="#FFFFFF"
    )
    # Arrow 2
    builder.add_badge(
        box=[812, 235, 20, 20],
        text="➔",
        gradient_colors=["#F87171", "#DC2626"],
        text_color="#FFFFFF",
        font_size=9,
        bold=True,
    )

    # KPI 3
    builder.add_kpi_card(
        box=grid_boxes[2],
        top_tag="成本刚性",
        value="9%降幅",
        bottom_badge="缺口6pp",
        theme_color="#DC2626",
        bg_color="#FEF5F5",
        border_color="#FECACA",
        tag_bg="#FFFFFF"
    )


# ==============================================================================
# BLOCK 4: Bottom Left Layered Clipboard (拟物板夹 + 表格 + 发光进度条)
# ==============================================================================
def add_clipboard_table_section(builder: SlideBuilder) -> None:
    """Render Block 4: Layered Clipboard Container, Native Data Table, and 5 Glowing Progress Bars."""
    # Baseline locked: left=32, top=315, width=438, height=605 (bottom=920)
    builder.add_card(
        box=[32, 315, 438, 605],
        gradient_colors=["#1E5AA0", "#2B78C9"],
        gradient_angle=135.0,
        border_color="#154A85",
        border_width_pt=1.5,
        radius=True,
    )

    # Top Metallic Clip Accent (3-Layer Photorealistic Clip)
    builder.add_card(box=[205, 303, 92, 18], bg_color="#64748B", border_color="#475569", border_width_pt=1.0, radius=True)
    builder.add_card(box=[212, 306, 78, 12], bg_color="#E2E8F0", border_color="#94A3B8", border_width_pt=0.8, radius=True)
    builder.add_card(box=[238, 309, 26, 6], bg_color="#475569", border_color="transparent", radius=True)

    # Inner White Paper Sheet (box: [40, 323, 422, 589])
    builder.add_card(
        box=[40, 323, 422, 589],
        bg_color="#FFFFFF",
        border_color="#CBD5E1",
        border_width_pt=1.0,
        radius=True,
    )

    # Paper Title: 核心战役完成度全景 (Strictly Centered, font_size=18 Bold at y: 338)
    builder.add_textbox(
        box=[40, 338, 422, 32],
        text="核心战役完成度全景",
        font_size=18,
        auto_fit_font=True,
        font_color="#0F172A",
        bold=True,
        align="center",
    )

    # Glossy Table Header Bar (at y: 376)
    builder.add_card(
        box=[48, 376, 406, 36],
        gradient_colors=["#428BD6", "#165096"],
        gradient_angle=90.0,
        radius=True,
        border_color="#18529C",
        border_width_pt=0.8,
    )
    # Header Column Titles (Crisp 11.5pt Bold White Text)
    builder.add_textbox(box=[62, 381, 80, 26], text="项目名称", font_size=11.5, font_color="#FFFFFF", bold=True, align="left")
    builder.add_textbox(box=[142, 381, 52, 26], text="目标值", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")
    builder.add_textbox(box=[194, 381, 52, 26], text="实际值", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")
    builder.add_textbox(box=[246, 381, 202, 26], text="整体完成率", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")

    # Zebra Row 2 & Row 4 Background Cards (Soft Peach)
    builder.add_card(box=[48, 484, 406, 56], bg_color="#FEF2F0", border_color="transparent", radius=True)
    builder.add_card(box=[48, 612, 406, 56], bg_color="#FEF2F0", border_color="transparent", radius=True)

    # 5 Data Rows: Labels, Targets, Actuals, and Progress Bars with strict vertical centering
    rows_data = [
        ("新用户招募", "45万", "38万", 0.84, "84%", 424),
        ("用户留存率", "70%", "69%", 0.99, "99%", 488),
        ("活动ROI", "1:5", "1:4:2", 0.84, "84%", 552),
        ("响应时效", "2.5h", "2.1h", 0.82, "82%", 616),
        ("用户调研量", "2500", "1620", 0.65, "65%", 680),
    ]

    for name_lbl, target_lbl, actual_lbl, pct_val, text_pct, y_start in rows_data:
        # Col 1: Name (Left Aligned)
        builder.add_textbox(box=[62, y_start + 6, 80, 28], text=name_lbl, font_size=11.5, font_color="#334155", align="left")
        # Col 2: Target (Centered)
        builder.add_textbox(box=[142, y_start + 6, 52, 28], text=target_lbl, font_size=11.5, font_color="#334155", align="center")
        # Col 3: Actual (Centered)
        builder.add_textbox(box=[194, y_start + 6, 52, 28], text=actual_lbl, font_size=11.5, font_color="#334155", align="center")
        # Col 4: Progress Bar + Percent Label (Vertically Centered with Text)
        builder.add_progress_bar(
            box=[248, y_start + 12, 146, 16],
            pct=pct_val,
            text=text_pct,
            bar_color="#C2410C",
            gradient_colors=["#8B2515", "#C2410C"],
            gradient_angle=90.0,
            bg_color="#FCE6DC",
            node_glow=True,
            font_size=10.5,
            text_color="#9A3412",
        )


# ==============================================================================
# BLOCK 5: Bottom Right Strategy Card (2+1 破局行动战略大卡 - 顶底严格锁齐)
# ==============================================================================
def add_strategy_card_section(builder: SlideBuilder) -> None:
    """Render Block 5: 2+1 Strategy Card with baseline locked to Block 4."""
    # Baseline locked: left=486, top=315, width=484, height=605 (bottom=920)
    builder.add_card(
        box=[486, 315, 484, 605],
        bg_color="#FFFFFF",
        border_color="#BAE6FD",
        border_width_pt=1.2,
        radius=True,
    )

    # Top Blue Gradient Header Bar (Horizontal Gradient: #2167BA -> #589CE3)
    builder.add_card(
        box=[486, 315, 484, 76],
        gradient_colors=["#2167BA", "#589CE3"],
        gradient_angle=0.0,
        border_color="transparent",
        radius=True,
    )

    # Strategy Title: "2+1" (Bold White 38pt) + "破局行动" (Bold White 22pt)
    builder.add_textbox(box=[496, 320, 84, 66], text="2+1", font_size=38, font_color="#FFFFFF", bold=True)
    builder.add_textbox(box=[580, 332, 116, 46], text="破局行动", font_size=21, font_color="#FFFFFF", bold=True)

    # Right Quote Pill Badge
    builder.add_badge(
        box=[702, 336, 256, 36],
        text="“在裂缝中寻找光，向结构要效率！”",
        bg_color="#143E75",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )

    # Action Section 1 (box: [494, 405, 468, 96])
    builder.add_flex_card(
        box=[494, 405, 468, 96],
        badge="1",
        badge_bg="#1456AA",
        badge_color="#FFFFFF",
        title="流量重构-突破渠道瓶颈",
        body_items=[
            "阶梯式缩量: 对低效渠道实施每周10%的预算递减机制",
            "建立新渠道试投池: 定向开发KOC种草、垂直社区等新型渠道，首批测试ROI达1:4.5"
        ],
        bg_color="#EDF6FD",
        border_color="transparent",
        radius=True,
    )

    # Action Section 2 (box: [494, 515, 468, 96])
    builder.add_flex_card(
        box=[494, 515, 468, 96],
        badge="2",
        badge_bg="#1456AA",
        badge_color="#FFFFFF",
        title="触点再造 - 激活沉默资产",
        body_items=[
            "黄金72小时: 对高价值用户推送专属权益包（含¥50无门槛券+会员体验）",
            "周期性刺激: 对中频用户每月推送品类专属优惠（美妆/母婴等定向满减）"
        ],
        bg_color="#EDF6FD",
        border_color="transparent",
        radius=True,
    )

    # Bottom Footer Container Bar (box: [486, 848, 484, 64])
    builder.add_card(
        box=[486, 848, 484, 64],
        bg_color="#EBF4FC",
        border_color="transparent",
        radius=True,
    )

    # Bottom Title Badge
    builder.add_badge(
        box=[496, 860, 142, 38],
        text="在存量战场挖掘增量价值",
        bg_color="#1D63B8",
        text_color="#FFFFFF",
        font_size=9.0,
        bold=True,
    )

    # Bottom 4 Keyword Pills: using add_grid for perfectly even distribution
    pill_boxes = builder.add_grid(box=[646, 860, 316, 38], cols=4, rows=1, gap_x=8.0)
    keywords = ["渠道洗牌", "沉默唤醒", "成本攻坚", "精准刀法"]
    for idx, p_box in enumerate(pill_boxes):
        builder.add_badge(
            box=list(p_box),
            text=keywords[idx],
            bg_color="#FFFFFF",
            text_color="#1E40AF",
            border_color="#93C5FD",
            font_size=8.5,
            bold=True,
        )


# ==============================================================================
# MAIN COMPOSER: build_slide_02
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
