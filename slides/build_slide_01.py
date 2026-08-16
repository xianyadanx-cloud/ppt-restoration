"""Slide 1 Construction Script: 问题分析与解决路径 (100% Pure Native Vector Implementation - Zero Images)

Follows SDD Spec (FEAT-PPT-002 Pure Vector Canvas-Calibrated):
- 100% Native PowerPoint Shapes & Freeform Polygons (Zero PNG / JPG images)
- Exact Canvas Proportions based on 16:9 Screen Calibration
- Rotated 3D Slanted Headers (±7.0°) & Center Poju Art + 3D Glass Sphere
- Symmetrical Mirror Alignment with High-Contrast Metric Highlights
"""

import os
import sys
import argparse
from typing import List, Optional, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder

def add_header_section(builder: SlideBuilder):
    # =============================================================
    # [HEADER BLOCK - 100% Native Vector Text & Shapes]
    # =============================================================
    # 1. Main Title
    builder.add_textbox(
        box=[35, 70, 500, 50],
        text="问题分析与解决路径",
        font_size=28,
        font_color="#000000",
        bold=True,
        align="left",
    )
    
    # 2. Author Tag
    builder.add_textbox(
        box=[820, 85, 145, 30],
        text="@鱼丸PPT",
        font_size=18,
        font_color="#334155",
        bold=True,
        align="right",
    )

    # 3. Horizontal Line
    builder.add_card(box=[35, 130, 930, 2], bg_color="#000000", border_color="transparent")

    # 4. Ribbon Container
    builder.add_card(
        box=[35, 160, 930, 45],
        bg_color="#FFFFFF",
        border_color="#93C5FD",
        border_width_pt=1.5,
    )
    # Left/Right Blue accents for the Ribbon
    builder.add_card(box=[35, 160, 10, 45], bg_color="#3B82F6", border_color="transparent")
    builder.add_card(box=[955, 160, 10, 45], bg_color="#3B82F6", border_color="transparent")

    # 5. Ribbon Text
    builder.add_textbox(
        box=[50, 160, 900, 45],
        text="“渠道渗透不足导致增量乏力，客户分层缺失影响转化效率，需构建精细化销售作战体系”",
        font_size=16,
        font_color="#1E293B",
        bold=True,
        align="center",
    )

def add_binder_base_section(builder: SlideBuilder):
    # =============================================================
    # [100% NATIVE VECTOR 3D FOLDER BASE - Polygons & Geometric Layers]
    # =============================================================
    # Bottom Ambient Ground Shadow
    builder.add_card(
        box=[60, 850, 880, 20],
        bg_color="#E2E8F0",
        border_color="transparent",
        radius=True,
    )

    # --- LEFT CYAN-BLUE 3D FOLDER BASE ---
    # Left Protruding Spine Tabs (3 step-tabs)
    builder.add_card(box=[50, 425, 40, 75], bg_color="#0284C7", border_color="transparent", radius=True)
    builder.add_card(box=[50, 575, 40, 75], bg_color="#0284C7", border_color="transparent", radius=True)
    builder.add_card(box=[50, 725, 40, 75], bg_color="#0284C7", border_color="transparent", radius=True)

    # Left 3D Spine Thickness
    builder.add_polygon(
        points=[(65, 255), (88, 280), (88, 830), (65, 805)],
        bg_color="#0369A1",
        border_color="transparent",
    )

    # Left 3D Top Slanted Thickness (Isometric Top Edge)
    builder.add_polygon(
        points=[(65, 255), (490, 310), (490, 328), (88, 280)],
        gradient_colors=["#0369A1", "#0284C7"],
        gradient_angle=90.0,
        border_color="transparent",
    )

    # Left Main Page Facing Panel (WHITE PAPER)
    builder.add_polygon(
        points=[(88, 280), (490, 328), (490, 878), (88, 830)],
        bg_color="#FFFFFF",
        border_color="#E0F2FE",
        border_width_pt=1.0,
    )

    # --- RIGHT BRICK-RED 3D FOLDER BASE ---
    # Right Protruding Spine Tabs (3 step-tabs)
    builder.add_card(box=[910, 425, 40, 75], bg_color="#991B1B", border_color="transparent", radius=True)
    builder.add_card(box=[910, 575, 40, 75], bg_color="#991B1B", border_color="transparent", radius=True)
    builder.add_card(box=[910, 725, 40, 75], bg_color="#991B1B", border_color="transparent", radius=True)

    # Right 3D Spine Thickness
    builder.add_polygon(
        points=[(912, 280), (935, 255), (935, 805), (912, 830)],
        bg_color="#7F1D1D",
        border_color="transparent",
    )

    # Right 3D Top Slanted Thickness (Isometric Top Edge)
    builder.add_polygon(
        points=[(510, 310), (935, 255), (912, 280), (510, 328)],
        gradient_colors=["#991B1B", "#7F1D1D"],
        gradient_angle=90.0,
        border_color="transparent",
    )

    # Right Main Page Facing Panel (WHITE PAPER)
    builder.add_polygon(
        points=[(510, 328), (912, 280), (912, 830), (510, 878)],
        bg_color="#FFFFFF",
        border_color="#FEE2E2",
        border_width_pt=1.0,
    )

    # --- CENTER SPINE CLEFT & 7 SPIRAL BINDER RINGS ---
    # Cleft Depth Shadow (Soft gradient instead of harsh black)
    builder.add_card(box=[485, 320, 30, 560], bg_color="#E2E8F0", border_color="transparent")

    # 7 Native Spiral Binder Loops (Shifted Left)
    spiral_y = [365, 440, 515, 590, 665, 740, 815]
    for sy in spiral_y:
        builder.add_card(box=[475, sy, 24, 14], bg_color="#475569", border_color="#CBD5E1", border_width_pt=1.0, radius=True)
        builder.add_card(box=[480, sy + 3, 14, 8], bg_color="#F8FAFC", border_color="transparent", radius=True)

def add_center_art_section(builder: SlideBuilder):
    # =============================================================
    # [CENTER ART: 存在问题 / 解决方案 / 破局 (Native Vector Art)]
    # =============================================================
    # Left Slanted Header Backer (Gradient on top of page)
    builder.add_polygon(
        points=[(88, 280), (490, 328), (490, 420), (88, 372)],
        gradient_colors=["#E0F2FE", "#FFFFFF"],
        gradient_angle=90.0,
        border_color="transparent",
    )
    # 1. "存在问题" Tilted Title
    builder.add_textbox(
        box=[130, 275, 300, 40],
        runs=[
            {"text": "存在问题 ", "size": 26, "bold": True, "color": "#0369A1"},
            {"text": "/ Existing Issues", "size": 14, "color": "#64748B"},
        ],
        align="left",
        rotation=-8.0,
    )

    # 2. "解决方案" Tilted Title
    builder.add_textbox(
        box=[520, 260, 350, 40],
        runs=[
            {"text": "Solution Strategies / ", "size": 14, "color": "#64748B"},
            {"text": "解决方案", "size": 26, "bold": True, "color": "#991B1B"},
        ],
        align="right",
        rotation=-8.0,
    )

    # 3. Native Speed Lines around "破"
    builder.add_card(box=[435, 220, 40, 35], bg_color="transparent", border_color="#334155", border_width_pt=2.0)

    # 4. The Giant "破局" Calligraphy (Native Text Box)
    builder.add_textbox(
        box=[415, 225, 150, 100],
        text="破局",
        font_size=52,
        font_color="#0F172A",
        bold=True,
        align="center",
        rotation=-12.0,
    )

    # 5. Native Gradient Sphere (Blue Bubble)
    builder.add_card(
        box=[530, 220, 20, 20],
        gradient_colors=["#7DD3FC", "#0284C7"],
        gradient_angle=45.0,
        border_color="transparent",
        radius=True,
    )


def add_left_problem_cards(builder: SlideBuilder):
    # =============================================================
    # [SUB-BANNERS: Native Rounded Ribbons with Pin Dots]
    # =============================================================
    # Left Sub-banner
    builder.add_card(box=[60, 370, 325, 30], bg_color="#E0F2FE", border_color="#7DD3FC", border_width_pt=1.0, radius=True)
    builder.add_card(box=[70, 379, 12, 12], bg_color="#0284C7", border_color="transparent", radius=True)
    builder.add_textbox(
        box=[87, 372, 290, 26],
        text="整体销售渠道渗透不足，导致客户转化低效",
        font_size=10,
        font_color="#0369A1",
        bold=True,
        align="left",
    )

    # =============================================================
    # [LEFT COLUMN: 存在问题 - 3 Native Raised Cards (Left Aligned)]
    # =============================================================
    # Left Card 1 (渠道管理粗放)
    builder.add_card(box=[45, 435, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[25, 422, 115, 26], text="渠道管理粗放", bg_color="#0284C7", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[55, 445, 320, 75],
        runs=[
            {"text": "3个重点区域渠道覆盖率", "size": 10.5, "color": "#334155"},
            {"text": "不足60%", "size": 10.5, "bold": True, "color": "#0284C7"},
            {"text": "，15%经销商月均产出", "size": 10.5, "color": "#334155"},
            {"text": "低于保本线", "size": 10.5, "bold": True, "color": "#E11D48"},
            {"text": "，渠道费用占比", "size": 10.5, "color": "#334155"},
            {"text": "超营收22%", "size": 10.5, "bold": True, "color": "#0284C7"},
        ],
        align="left",
    )

    # Left Card 2 (客户分层模糊)
    builder.add_card(box=[45, 555, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[25, 542, 115, 26], text="客户分层模糊", bg_color="#0284C7", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[55, 565, 320, 75],
        runs=[
            {"text": "未建立客户价值评估模型，A类客户签单周期", "size": 10.5, "color": "#334155"},
            {"text": "长达45天", "size": 10.5, "bold": True, "color": "#0284C7"},
            {"text": "，二次转化率较行业均值", "size": 10.5, "color": "#334155"},
            {"text": "低18%", "size": 10.5, "bold": True, "color": "#E11D48"},
        ],
        align="left",
    )

    # Left Card 3 (竞品响应滞后)
    builder.add_card(box=[45, 675, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[25, 662, 115, 26], text="竞品响应滞后", bg_color="#0284C7", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[55, 685, 320, 75],
        runs=[
            {"text": "竞品新品上市平均", "size": 10.5, "color": "#334155"},
            {"text": "7天才启动应对", "size": 10.5, "bold": True, "color": "#0284C7"},
            {"text": "相应策略，其中价格调整响应延迟导致", "size": 10.5, "color": "#334155"},
            {"text": "3%市占率流失", "size": 10.5, "bold": True, "color": "#E11D48"},
        ],
        align="left",
    )


def add_right_solution_cards(builder: SlideBuilder):
    # Right Sub-banner
    builder.add_card(box=[615, 370, 325, 30], bg_color="#FEF2F2", border_color="#FECACA", border_width_pt=1.0, radius=True)
    builder.add_card(box=[915, 379, 12, 12], bg_color="#991B1B", border_color="transparent", radius=True)
    builder.add_textbox(
        box=[625, 372, 280, 26],
        text="实施精准拓客增效，利用动态攻防提速",
        font_size=10,
        font_color="#991B1B",
        bold=True,
        align="right",
    )

    # =============================================================
    # [RIGHT COLUMN: 解决方案 - 3 Native Raised Cards (Right Aligned)]
    # =============================================================
    # Right Card 1 (渠道网格化精耕)
    builder.add_card(box=[615, 435, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[845, 422, 125, 26], text="渠道网格化精耕", bg_color="#991B1B", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[625, 445, 320, 75],
        runs=[
            {"text": "划分", "size": 10.5, "color": "#334155"},
            {"text": "5大作战网格", "size": 10.5, "bold": True, "color": "#991B1B"},
            {"text": "，建立「铁三角」驻点帮扶机制，目标3个月内优质渠道覆盖率", "size": 10.5, "color": "#334155"},
            {"text": "提升至85%", "size": 10.5, "bold": True, "color": "#16A34A"},
        ],
        align="right",
    )

    # Right Card 2 (客户价值分级)
    builder.add_card(box=[615, 555, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[845, 542, 125, 26], text="客户价值分级", bg_color="#991B1B", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[625, 565, 320, 75],
        runs=[
            {"text": "上线", "size": 10.5, "color": "#334155"},
            {"text": "LTV预测模型", "size": 10.5, "bold": True, "color": "#991B1B"},
            {"text": "，制定钻石/黄金/白银三级服务标准，缩短A类客户签单周期", "size": 10.5, "color": "#334155"},
            {"text": "至30天内", "size": 10.5, "bold": True, "color": "#16A34A"},
        ],
        align="right",
    )

    # Right Card 3 (竞品监测反制)
    builder.add_card(box=[615, 675, 340, 90], bg_color="#FFFFFF", border_color="#E2E8F0", border_width_pt=1.0, radius=True)
    builder.add_badge(box=[845, 662, 125, 26], text="竞品监测反制", bg_color="#991B1B", text_color="#FFFFFF", font_size=10, bold=True)
    builder.add_textbox(
        box=[625, 685, 320, 75],
        runs=[
            {"text": "搭建动态监测系统，设置价格/新品/促销", "size": 10.5, "color": "#334155"},
            {"text": "三重预警机制", "size": 10.5, "bold": True, "color": "#991B1B"},
            {"text": "，确保", "size": 10.5, "color": "#334155"},
            {"text": "72小时内", "size": 10.5, "bold": True, "color": "#16A34A"},
            {"text": "输出定制化应对方案", "size": 10.5, "color": "#334155"},
        ],
        align="right",
    )


def build_slide_01(
    active_blocks: Optional[List[str]] = None,
    cumulative_up_to: Optional[Union[int, str]] = None,
    output_path: str = "output/slide_01.pptx",
):
    print("=" * 60)
    print("🚀 100% Pure Native Vector Reconstructing Slide 01 (ZERO IMAGES)")
    print("=" * 60)

    builder = SlideBuilder(aspect_ratio="16:9", bg_color="#F8FAFC")

    block_map = {
        "header": ("Block 1 [Header]", add_header_section),
        "binder": ("Block 2 [3D Binder Base]", add_binder_base_section),
        "center_art": ("Block 3 [Center Art]", add_center_art_section),
        "left_cards": ("Block 4 [Left Cards]", add_left_problem_cards),
        "right_cards": ("Block 5 [Right Cards]", add_right_solution_cards),
    }
    all_keys = ["header", "binder", "center_art", "left_cards", "right_cards"]

    if cumulative_up_to is not None:
        if str(cumulative_up_to).isdigit():
            limit_idx = int(cumulative_up_to)
        else:
            limit_idx = all_keys.index(str(cumulative_up_to).lower()) + 1
        target_blocks = all_keys[:limit_idx]
    elif active_blocks is None:
        target_blocks = all_keys
    else:
        target_blocks = [b.lower() for b in active_blocks]

    for key in target_blocks:
        if key in block_map:
            name, func = block_map[key]
            print(f"🔧 Building {name}...")
            func(builder)

    builder.save(output_path)
    print(f"🎉 Successfully built Slide 01 (100% Pure Native Vector): {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Slide 01")
    parser.add_argument("-o", "--output", default="output/slide_01.pptx", help="Output PPTX path")
    parser.add_argument("--blocks", nargs="+", help="Specific blocks to render")
    parser.add_argument("--cumulative-up-to", help="Render all blocks up to this index (1-based) or name")
    args = parser.parse_args()

    build_slide_01(
        active_blocks=args.blocks,
        cumulative_up_to=args.cumulative_up_to,
        output_path=args.output,
    )
