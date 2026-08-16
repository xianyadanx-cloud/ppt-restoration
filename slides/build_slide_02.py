"""Slide 2 Precise Restoration Script: 季度工作攻坚策略 (100% Native Pure Vector Architecture)

Exact Geometric Alignment with Ground Truth:
- Block 1: [26, 26, 948, 62] Header & Author Tag
- Block 2: [26, 98, 948, 66] Top Summary Banner
- Block 3: [26, 178, 948, 112] Middle Subtitle & 3 Composite KPI Cards
- Block 4: [26, 305, 456, 620] Left Realistic Layered Clipboard + Table + Progress Bars
- Block 5: [498, 305, 476, 620] Right 2+1 Strategy Card + Title Strips + Plain Text Lists + Footer Pills
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
    # Main Title: "季度工作攻坚策略" (GT: left=26, top=26, 28pt Bold Black)
    builder.add_textbox(
        box=[26, 26, 600, 48],
        text="季度工作攻坚策略",
        font_size=28,
        auto_fit_font=True,
        font_color="#0F172A",
        bold=True,
    )
    # Underline Divider Line (GT: left=26, top=82, width=948, 0.75pt Light Gray)
    builder.add_card(box=[26, 82, 948, 1.0], bg_color="#E2E8F0", border_color="transparent")
    # Right Author Tag: "@鱼丸PPT" (GT: right=974, top=32, 16pt Bold)
    builder.add_textbox(
        box=[720, 32, 254, 40],
        text="@鱼丸PPT",
        font_size=16,
        auto_fit_font=True,
        font_color="#0F172A",
        bold=True,
        align="right",
    )


# ==============================================================================
# BLOCK 2: Top Summary Banner (总览概述胶囊横幅)
# ==============================================================================
def add_summary_banner_section(builder: SlideBuilder) -> None:
    """Render Block 2: Top Overview Summary Banner with Gradient Badge and Structured Runs."""
    # Outer Background Container: [26, 96, 948, 64]
    builder.add_card(
        box=[26, 96, 948, 64],
        bg_color="#EDF5FD",
        border_color="#D0E3F7",
        border_width_pt=0.8,
        radius=True,
    )
    # Left Gradient Deep Blue Badge: [26, 96, 68, 64]
    builder.add_card(
        box=[26, 96, 68, 64],
        gradient_colors=["#1B5B9E", "#2D78C8"],
        gradient_angle=135.0,
        border_color="transparent",
        radius=True,
    )
    builder.add_textbox(
        box=[26, 106, 68, 44],
        text="总览\n概述",
        font_size=13,
        font_color="#FFFFFF",
        bold=True,
        align="center",
    )
    # Right Rich Text Description: starts at left=106, width=856
    builder.add_textbox(
        box=[104, 101, 858, 54],
        runs=[
            {"text": "本季度聚焦用户质量提升，核心指标达成率", "size": 10.5, "color": "#334155"},
            {"text": "89%", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "，同比增幅收窄至", "size": 10.5, "color": "#334155"},
            {"text": "3%", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "。通过重构活动投放策略，注册用户转化成本", "size": 10.5, "color": "#334155"},
            {"text": "降低21%", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "，但新客规模\n", "size": 10.5, "color": "#334155"},
            {"text": "缺口达12%", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "，付费转化率", "size": 10.5, "color": "#334155"},
            {"text": "6.1%（目标6.5%）", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "，运营成本", "size": 10.5, "color": "#334155"},
            {"text": "降幅9%（目标15%）", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "。", "size": 10.5, "color": "#334155"},
        ],
    )


# ==============================================================================
# BLOCK 3: Middle Subtitle & 3 Composite KPI Cards (多维度运营效能透视与指标卡)
# ==============================================================================
def add_mid_kpi_section(builder: SlideBuilder) -> None:
    """Render Block 3: Subtitle, Descriptive Summary, and 3 Stacked KPI Metric Cards with Flow Arrows."""
    # Left Subtitle: [26, 178, 440, 28]
    builder.add_textbox(
        box=[26, 178, 440, 28],
        text="多维度运营效能透视",
        font_size=17,
        font_color="#0F172A",
        bold=True,
    )
    # Left Description Text: [26, 208, 440, 56]
    builder.add_textbox(
        box=[26, 208, 440, 56],
        runs=[
            {"text": "推行精准获客策略后，高净值用户占比突破", "size": 10.0, "color": "#64748B"},
            {"text": "40%（+8pp）", "size": 10.0, "bold": True, "color": "#334155"},
            {"text": "，但新用户总量仅达成\n", "size": 10.0, "color": "#64748B"},
            {"text": "38万（目标45万）", "size": 10.0, "bold": True, "color": "#334155"},
            {"text": "。会员权益升级拉动复购率提升至", "size": 10.0, "color": "#64748B"},
            {"text": "19%（目标22%）", "size": 10.0, "bold": True, "color": "#334155"},
        ],
    )

    # Right 3 Composite KPI Cards: [498, 178, 476, 98]
    # Card 1: 规模缺口 -> [502, 178, 126, 96]
    builder.add_card(box=[502, 186, 126, 88], bg_color="#F0F7FD", border_color="#BAE6FD", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[525, 174, 80, 22], text="规模缺口", bg_color="#FFFFFF", border_color="#3880C9", text_color="#1B5B9E", font_size=9.5, bold=True)
    builder.add_textbox(box=[502, 202, 126, 36], text="38万", font_size=20, font_color="#0F172A", bold=True, align="center")
    builder.add_card(box=[522, 244, 86, 22], gradient_colors=["#1B5B9E", "#2D78C8"], gradient_angle=90.0, border_color="transparent", radius=True)
    builder.add_textbox(box=[522, 244, 86, 22], text="缺口16%", font_size=9.5, font_color="#FFFFFF", bold=True, align="center")

    # Arrow 1: [642, 220, 22, 22]
    builder.add_card(box=[642, 220, 22, 22], gradient_colors=["#60A5FA", "#2563EB"], gradient_angle=135.0, border_color="transparent", radius=True)
    builder.add_textbox(box=[642, 220, 22, 22], text="➔", font_size=10, font_color="#FFFFFF", bold=True, align="center")

    # Card 2: 转化迟滞 -> [676, 178, 126, 96]
    builder.add_card(box=[676, 186, 126, 88], bg_color="#F0F7FD", border_color="#BAE6FD", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[699, 174, 80, 22], text="转化迟滞", bg_color="#FFFFFF", border_color="#3880C9", text_color="#1B5B9E", font_size=9.5, bold=True)
    builder.add_textbox(box=[676, 202, 126, 36], text="6.1%", font_size=20, font_color="#0F172A", bold=True, align="center")
    builder.add_card(box=[696, 244, 86, 22], gradient_colors=["#1B5B9E", "#2D78C8"], gradient_angle=90.0, border_color="transparent", radius=True)
    builder.add_textbox(box=[696, 244, 86, 22], text="缺口0.4pp", font_size=9.5, font_color="#FFFFFF", bold=True, align="center")

    # Arrow 2: [816, 220, 22, 22]
    builder.add_card(box=[816, 220, 22, 22], gradient_colors=["#F87171", "#DC2626"], gradient_angle=135.0, border_color="transparent", radius=True)
    builder.add_textbox(box=[816, 220, 22, 22], text="➔", font_size=10, font_color="#FFFFFF", bold=True, align="center")

    # Card 3: 成本刚性 -> [850, 178, 124, 96]
    builder.add_card(box=[850, 186, 124, 88], bg_color="#FEF5F5", border_color="#FECACA", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[872, 174, 80, 22], text="成本刚性", bg_color="#FFFFFF", border_color="#E05238", text_color="#C2410C", font_size=9.5, bold=True)
    builder.add_textbox(box=[850, 202, 124, 36], text="9%降幅", font_size=20, font_color="#0F172A", bold=True, align="center")
    builder.add_card(box=[869, 244, 86, 22], gradient_colors=["#C2410C", "#DC2626"], gradient_angle=90.0, border_color="transparent", radius=True)
    builder.add_textbox(box=[869, 244, 86, 22], text="缺口6pp", font_size=9.5, font_color="#FFFFFF", bold=True, align="center")


# ==============================================================================
# BLOCK 4: Bottom Left Layered Clipboard (拟物板夹 + 表格 + 发光进度条)
# ==============================================================================
def add_clipboard_table_section(builder: SlideBuilder) -> None:
    """Render Block 4: Layered Clipboard Container, Native Data Table, and 5 Glowing Progress Bars."""
    # Baseline locked: left=26, top=305, width=456, height=620 (bottom=925)
    builder.add_card(
        box=[26, 305, 456, 620],
        gradient_colors=["#1B5B9E", "#2D78C8"],
        gradient_angle=135.0,
        border_color="#144A85",
        border_width_pt=1.5,
        radius=True,
    )

    # Top Metallic Clip Accent (Photorealistic Clip)
    builder.add_card(box=[208, 292, 92, 20], bg_color="#64748B", border_color="#475569", border_width_pt=1.0, radius=True)
    builder.add_card(box=[215, 296, 78, 12], bg_color="#E2E8F0", border_color="#94A3B8", border_width_pt=0.8, radius=True)
    builder.add_card(box=[241, 299, 26, 6], bg_color="#475569", border_color="transparent", radius=True)

    # Inner White Paper Sheet: [34, 313, 440, 604]
    builder.add_card(
        box=[34, 313, 440, 604],
        bg_color="#FFFFFF",
        border_color="#CBD5E1",
        border_width_pt=1.0,
        radius=True,
    )

    # Paper Title: 核心战役完成度全景 (Strictly Centered, font_size=18 Bold at y: 330)
    builder.add_textbox(
        box=[34, 330, 440, 32],
        text="核心战役完成度全景",
        font_size=18,
        auto_fit_font=True,
        font_color="#0F172A",
        bold=True,
        align="center",
    )

    # Glossy Table Header Bar (at y: 370)
    builder.add_card(
        box=[44, 370, 420, 36],
        gradient_colors=["#3A84D2", "#18529C"],
        gradient_angle=90.0,
        radius=True,
        border_color="#18529C",
        border_width_pt=0.8,
    )
    # Header Column Titles (Crisp 11.5pt Bold White Text)
    builder.add_textbox(box=[56, 375, 84, 26], text="项目名称", font_size=11.5, font_color="#FFFFFF", bold=True, align="left")
    builder.add_textbox(box=[144, 375, 52, 26], text="目标值", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")
    builder.add_textbox(box=[200, 375, 52, 26], text="实际值", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")
    builder.add_textbox(box=[256, 375, 200, 26], text="整体完成率", font_size=11.5, font_color="#FFFFFF", bold=True, align="center")

    # Zebra Row 2 & Row 4 Background Cards (Soft Peach)
    builder.add_card(box=[44, 482, 420, 56], bg_color="#FEF3F2", border_color="transparent", radius=True)
    builder.add_card(box=[44, 614, 420, 56], bg_color="#FEF3F2", border_color="transparent", radius=True)

    # 5 Data Rows: Labels, Targets, Actuals, and Progress Bars with strict vertical centering
    rows_data = [
        ("新用户招募", "45万", "38万", 0.84, "84%", 420),
        ("用户留存率", "70%", "69%", 0.99, "99%", 486),
        ("活动ROI", "1:5", "1:4:2", 0.84, "84%", 552),
        ("响应时效", "2.5h", "2.1h", 0.82, "82%", 618),
        ("用户调研量", "2500", "1620", 0.65, "65%", 684),
    ]

    for name_lbl, target_lbl, actual_lbl, pct_val, text_pct, y_start in rows_data:
        # Col 1: Name (Left Aligned)
        builder.add_textbox(box=[56, y_start + 6, 84, 28], text=name_lbl, font_size=11.5, font_color="#334155", align="left")
        # Col 2: Target (Centered)
        builder.add_textbox(box=[144, y_start + 6, 52, 28], text=target_lbl, font_size=11.5, font_color="#334155", align="center")
        # Col 3: Actual (Centered)
        builder.add_textbox(box=[200, y_start + 6, 52, 28], text=actual_lbl, font_size=11.5, font_color="#334155", align="center")
        # Col 4: Progress Bar + Percent Label (Vertically Centered with Text)
        builder.add_progress_bar(
            box=[258, y_start + 12, 150, 16],
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
# BLOCK 5: Bottom Right Strategy Card (2+1 破局行动战略大卡 - 100% 纯正版式还原)
# ==============================================================================
def add_strategy_card_section(builder: SlideBuilder) -> None:
    """Render Block 5: 2+1 Strategy Card with pure white card surface and title strips."""
    # Baseline locked: left=498, top=305, width=476, height=620 (bottom=925)
    # 1. Main Outer Card Container (White with subtle sky-blue border)
    builder.add_card(
        box=[498, 305, 476, 620],
        bg_color="#FFFFFF",
        border_color="#BAE6FD",
        border_width_pt=1.2,
        radius=True,
    )

    # 2. Top Blue Gradient Header Bar (Horizontal Gradient: #1B5B9E -> #4A90E2)
    builder.add_card(
        box=[498, 305, 476, 76],
        gradient_colors=["#1B5B9E", "#4A90E2"],
        gradient_angle=0.0,
        border_color="transparent",
        radius=True,
    )

    # Strategy Title: "2+1" (Bold White 38pt) + "破局行动" (Bold White 22pt)
    builder.add_textbox(box=[508, 310, 84, 66], text="2+1", font_size=38, font_color="#FFFFFF", bold=True)
    builder.add_textbox(box=[592, 322, 116, 46], text="破局行动", font_size=21, font_color="#FFFFFF", bold=True)

    # Right Quote Pill Badge
    builder.add_badge(
        box=[712, 326, 250, 34],
        text="“在裂缝中寻找光，向结构要效率！”",
        bg_color="#143E75",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )

    # --------------------------------------------------------------------------
    # Action Section 1: Floating White Action Card Container (y=396 to y=600, h=204)
    # --------------------------------------------------------------------------
    # White Card 1 Baseplate
    builder.add_card(box=[506, 396, 460, 204], bg_color="#FFFFFF", border_color="#D1E4F7", border_width_pt=1.0, radius=True)
    # Title Strip 1 inside White Card: [512, 402, 448, 38]
    builder.add_card(box=[512, 402, 448, 38], bg_color="#EBF4FD", border_color="transparent", radius=True)
    # Number 1 Circle Badge (Mathematic Circle: 26x26)
    builder.add_badge(box=[518, 408, 26, 26], text="1", bg_color="#1B5B9E", text_color="#FFFFFF", font_size=11.5, bold=True)
    # Title 1 Text
    builder.add_textbox(box=[552, 406, 400, 30], text="流量重构-突破渠道瓶颈", font_size=13.5, font_color="#0F172A", bold=True)
    # Bullet List 1 (Inside White Card, spacious line height & padding)
    builder.add_textbox(
        box=[518, 452, 436, 136],
        runs=[
            {"text": "•  阶梯式缩量: ", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "对低效渠道实施每周10%的预算递减机制\n\n", "size": 10.0, "color": "#475569"},
            {"text": "•  建立新渠道试投池: ", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "定向开发KOC种草、垂直社区等新型渠道，首批测试ROI达1:4.5", "size": 10.0, "color": "#475569"},
        ],
    )

    # --------------------------------------------------------------------------
    # Action Section 2: Floating White Action Card Container (y=616 to y=820, h=204)
    # --------------------------------------------------------------------------
    # White Card 2 Baseplate
    builder.add_card(box=[506, 616, 460, 204], bg_color="#FFFFFF", border_color="#D1E4F7", border_width_pt=1.0, radius=True)
    # Title Strip 2 inside White Card: [512, 622, 448, 38]
    builder.add_card(box=[512, 622, 448, 38], bg_color="#EBF4FD", border_color="transparent", radius=True)
    # Number 2 Circle Badge (Mathematic Circle: 26x26)
    builder.add_badge(box=[518, 628, 26, 26], text="2", bg_color="#1B5B9E", text_color="#FFFFFF", font_size=11.5, bold=True)
    # Title 2 Text
    builder.add_textbox(box=[552, 626, 400, 30], text="触点再造 - 激活沉默资产", font_size=13.5, font_color="#0F172A", bold=True)
    # Bullet List 2 (Inside White Card, spacious line height & padding)
    builder.add_textbox(
        box=[518, 672, 436, 136],
        runs=[
            {"text": "•  黄金72小时: ", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "对高价值用户推送专属权益包（含¥50无门槛券+会员体验）\n\n", "size": 10.0, "color": "#475569"},
            {"text": "•  周期性刺激: ", "size": 10.5, "bold": True, "color": "#0F172A"},
            {"text": "对中频用户每月推送品类专属优惠（美妆/母婴等定向满减）", "size": 10.0, "color": "#475569"},
        ],
    )

    # --------------------------------------------------------------------------
    # Footer Section: Blue Bottom Bar + Title Badge + 4 Keyword Pills
    # --------------------------------------------------------------------------
    # Bottom Footer Container Bar: [498, 838, 476, 80]
    builder.add_card(
        box=[498, 838, 476, 80],
        bg_color="#EBF4FC",
        border_color="transparent",
        radius=True,
    )

    # Bottom Title Badge: [506, 856, 144, 44]
    builder.add_badge(
        box=[506, 856, 144, 44],
        text="在存量战场挖掘增量价值",
        bg_color="#1B5B9E",
        text_color="#FFFFFF",
        font_size=9.5,
        bold=True,
    )

    # Bottom 4 Keyword Pills: using add_grid for perfectly even distribution
    pill_boxes = builder.add_grid(box=[656, 856, 308, 44], cols=4, rows=1, gap_x=8.0)
    keywords = ["渠道洗牌", "沉默唤醒", "成本攻坚", "精准刀法"]
    for idx, p_box in enumerate(pill_boxes):
        builder.add_badge(
            box=list(p_box),
            text=keywords[idx],
            bg_color="#FFFFFF",
            text_color="#1B5B9E",
            border_color="#93C5FD",
            font_size=9.0,
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
