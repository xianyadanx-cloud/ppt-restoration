"""Slide Construction Script for sample_slide

Auto-generated scaffold. Follow AGENTS.md SOP:
1. Macro Blueprint Gate: Plan [left, top, width, height] for each block.
2. Slicing: Crop any bitmap images using tools/slice.py if needed.
3. Native Elements: Build header, cards, native charts, tables, and typography.
4. Verify: Run `python tools/verify.py input/sample_slide.png output/sample_slide.pptx`
"""

import os
import sys

# Ensure tools package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


def build_slide():
    # 1. Initialize builder from source image (auto-detects 16:9 / 4:3)
    builder = SlideBuilder.from_image("input/sample_slide.png", bg_color="#F8FAFC")

    # 2. Header Block
    builder.add_header(
        title="Slide Title Goes Here",
        subtitle="Supporting subtitle or narrative explanation",
        category_tag="CATEGORY",
        box=[40, 35, 920, 100],
    )

    # 3. Content Blocks (e.g., Cards, Text, Native Charts, Native Tables)
    # Example Card Container
    builder.add_card(box=[40, 160, 440, 520], bg_color="#FFFFFF", border_color="#E2E8F0", radius=True)
    builder.add_textbox(
        box=[60, 180, 400, 480],
        runs=[
            {"text": "01 Key Pillar\n", "size": 15, "bold": True, "color": "#0F172A"},
            {"text": "Add descriptive details, metrics, and structured insights here.\n\n", "size": 11, "color": "#475569"},
        ]
    )

    # Example Chart / Table or Second Card
    builder.add_card(box=[520, 160, 440, 520], bg_color="#FFFFFF", border_color="#E2E8F0", radius=True)
    builder.add_chart(
        box=[540, 180, 400, 480],
        chart_type="column",
        categories=["Q1", "Q2", "Q3", "Q4"],
        series=[{"name": "Performance", "values": [45, 68, 85, 110]}],
        title="Performance Trend",
    )

    # 4. Save PPTX
    output_path = "output/sample_slide.pptx"
    builder.save(output_path)
    return output_path


if __name__ == "__main__":
    build_slide()
