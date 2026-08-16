import sys

with open('slides/build_slide_02.py', 'r') as f:
    content = f.read()

content = content.replace(
    'from tools.pptx_helper import SlideBuilder',
    'from tools.pptx_helper import SlideBuilder, Tokens'
)

# Header
content = content.replace(
    'font_size=36,',
    'font_size=Tokens.FONT_HERO,\n        auto_fit_font=True,'
)
content = content.replace(
    'font_size=20,',
    'font_size=Tokens.FONT_TITLE_MD,\n        auto_fit_font=True,'
)

# Block 3 KPIs
old_kpis = """    # --- KPI Card 1: 规模缺口 ---
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
    )"""

new_kpis = """    # Generate 3 columns grid for KPI cards
    grid_boxes = builder.add_grid(box=[515, 192, 457, 105], cols=3, rows=1, gap_x=40)

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
        box=[650, 236, 22, 22],
        text="➔",
        gradient_colors=["#60A5FA", "#2563EB"],
        text_color="#FFFFFF",
        font_size=10,
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
        box=[820, 236, 22, 22],
        text="➔",
        gradient_colors=["#F87171", "#DC2626"],
        text_color="#FFFFFF",
        font_size=10,
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
    )"""
content = content.replace(old_kpis, new_kpis)

# Strategy Section Action 1 & 2
old_actions = """    # 3. Action Section 1
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
    builder.add_textbox(box=[500, 588, 600, 22], text="• 周期性刺激: 对中频用户每月推送品类专属优惠（美妆/母婴等定向满减）", font_size=10.5, font_color="#334155", word_wrap=False)"""

new_actions = """    # 3. Action Section 1 using add_flex_card
    builder.add_flex_card(
        box=[488, 412, 474, 98],
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

    # 4. Action Section 2 using add_flex_card
    builder.add_flex_card(
        box=[488, 518, 474, 98],
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
    )"""
content = content.replace(old_actions, new_actions)


# Footer Stack
old_footer = """    pills = ["渠道洗牌", "沉默唤醒", "成本攻坚", "精准刀法"]
    for i, p_txt in enumerate(pills):
        builder.add_badge(
            box=[648 + i * 82, 856, 72, 38],
            text=p_txt,
            bg_color="#FFFFFF",
            border_color="#93C5FD",
            text_color="#1E40AF",
            font_size=9.5,
            bold=True,
        )"""

new_footer = """    # Footer Pills using add_stack
    builder.add_stack(
        box=[648, 856, 320, 38],
        direction="horizontal",
        gap=8.0,
        children=[
            {"type": "badge", "text": p, "bg_color": "#FFFFFF", "text_color": "#1E40AF", "border_color": "#93C5FD", "width": 72, "height": 38}
            for p in ["渠道洗牌", "沉默唤醒", "成本攻坚", "精准刀法"]
        ],
        bg_color="transparent",
        border_color="transparent",
    )"""
content = content.replace(old_footer, new_footer)

with open('slides/build_slide_02.py', 'w') as f:
    f.write(content)
