"""Standard Reference Example: Reconstructing sample_slide.png to native PPTX.

Demonstrates the 4 Quality Gates and SlideBuilder API for Coding Agents:
- Gate 1: Palette extraction (#F8FAFC, #2563EB, #0F172A, #64748B)
- Gate 2: Macro Blueprint planning in 0-1000 coordinates
- Gate 3: Native editable cards, typography, native bar chart, table, and sliced logo
- Gate 4: Visual verification
"""

import os
import sys

# Ensure workspace tools are accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder
from tools.slice import slice_image


def build_sample_presentation(
    input_image: str = "examples/sample_slide.png",
    output_pptx: str = "examples/sample_output.pptx",
):
    print("=" * 60)
    print(f"🏗️  Reconstructing: {input_image} -> {output_pptx}")
    print("=" * 60)

    # -------------------------------------------------------------
    # [Gate 1 & 2] Palette & Macro Blueprint
    # -------------------------------------------------------------
    # Blueprint in 0-1000 scale:
    # Header:       [40, 35, 800, 140]
    # Top-right:    [890, 45, 65, 95] (Bitmap logo crop)
    # Card 1 (Left):   [40, 200, 290, 680] (Key capabilities & metric)
    # Card 2 (Middle): [355, 200, 290, 680] (Native quarterly bar chart)
    # Card 3 (Right):  [670, 200, 290, 680] (Native milestone table)
    # -------------------------------------------------------------

    # 1. Initialize SlideBuilder from source image
    builder = SlideBuilder.from_image(input_image, bg_color="#F8FAFC")

    # 2. Add Header with Category Tag and Subtitle
    builder.add_header(
        title="AI Agentic Automation Platform",
        subtitle="Driving operational excellence through native multimodal reconstruction",
        category_tag="STRATEGY 2026",
        box=[40, 45, 820, 130],
        title_size=24,
        subtitle_size=12,
        title_color="#0F172A",
        subtitle_color="#64748B",
        tag_color="#2563EB",
        tag_bg="#DBEAFE",
    )

    # 3. Crop and Insert Top-Right Logo (Strict Gate 3: Slicing bitmap assets only)
    logo_crop_path = "assets/sample_logo.png"
    slice_image(input_image, box=[890, 50, 65, 115], output_path=logo_crop_path)
    builder.add_image(box=[890, 50, 65, 115], image_path=logo_crop_path)

    # =============================================================
    # [CARD 1: Left Pillar & Key Capabilities]
    # =============================================================
    builder.add_card(
        box=[40, 200, 290, 680],
        bg_color="#FFFFFF",
        border_color="#E2E8F0",
        border_width_pt=1.0,
        radius=True,
    )
    # Card 1 Title & Narrative
    builder.add_textbox(
        box=[55, 220, 260, 90],
        runs=[
            {"text": "01 Core Capabilities\n", "size": 15, "bold": True, "color": "#0F172A"},
            {"text": "Key strategic pillars for autonomous slide generation:\n", "size": 10, "color": "#64748B"},
        ]
    )
    # Card 1 Bullet List
    builder.add_bullet_list(
        box=[55, 320, 260, 310],
        items=[
            {"title": "Native Reconstruction", "text": "True PowerPoint shapes, textframes, and tables."},
            {"title": "Quality Gates", "text": "Enforces strict style, blueprint, and typography checks."},
            {"title": "Visual Verification", "text": "Automates side-by-side diffing and inspection."},
            {"title": "Zero Bottleneck", "text": "Runs directly on terminal with local python tools."},
        ],
        font_size=10,
        space_after_pt=8,
    )
    # Card 1 Highlight Metric Box (Nested Card)
    builder.add_card(
        box=[55, 650, 260, 200],
        bg_color="#EEF2FF",
        border_color="#C7D2FE",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_textbox(
        box=[68, 665, 235, 170],
        runs=[
            {"text": "EFFICIENCY GAIN\n", "size": 9, "bold": True, "color": "#4F46E5"},
            {"text": "85% Faster Turnaround\n", "size": 14, "bold": True, "color": "#1E1B4B"},
            {"text": "vs traditional manual PowerPoint drafting", "size": 10, "color": "#64748B"},
        ]
    )

    # =============================================================
    # [CARD 2: Middle Quarterly Performance Native Chart]
    # =============================================================
    builder.add_card(
        box=[355, 200, 290, 680],
        bg_color="#FFFFFF",
        border_color="#E2E8F0",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_textbox(
        box=[370, 220, 260, 80],
        runs=[
            {"text": "02 Quarterly Performance\n", "size": 15, "bold": True, "color": "#0F172A"},
            {"text": "Slide deck restoration volume by quarter (2026)", "size": 10, "color": "#64748B"},
        ]
    )
    # Native PowerPoint Bar/Column Chart
    builder.add_chart(
        box=[370, 310, 260, 540],
        chart_type="column",
        categories=["Q1", "Q2", "Q3", "Q4"],
        series=[{"name": "Decks Restored", "values": [120, 210, 340, 480]}],
        has_legend=False,
    )

    # =============================================================
    # [CARD 3: Right Execution Milestones Native Table]
    # =============================================================
    builder.add_card(
        box=[670, 200, 290, 680],
        bg_color="#FFFFFF",
        border_color="#E2E8F0",
        border_width_pt=1.0,
        radius=True,
    )
    builder.add_textbox(
        box=[685, 220, 260, 80],
        runs=[
            {"text": "03 Execution Milestones\n", "size": 15, "bold": True, "color": "#0F172A"},
            {"text": "Tracked delivery stages & completion metrics", "size": 10, "color": "#64748B"},
        ]
    )
    # Native PowerPoint Table with styled headers and zebra striping
    builder.add_table(
        box=[685, 310, 260, 540],
        headers=["Milestone", "Owner", "Status"],
        rows=[
            ["M1 Blueprint", "Agent", "Done (100%)"],
            ["M2 Native PPTX", "Agent", "Done (100%)"],
            ["M3 Verification", "Verify", "Passed"],
            ["M4 Multi-Merge", "Merge", "Ready"],
            ["M5 Final Delivery", "Team", "Active"],
        ],
        col_widths=[110, 70, 80],
        header_bg="#0F172A",
        header_color="#FFFFFF",
        alt_row_bg="#F8FAFC",
        font_size=9,
    )

    # 4. Save final output
    builder.save(output_pptx)
    # Also save to output/ for quick verify
    os.makedirs("output", exist_ok=True)
    builder.save("output/sample_slide.pptx")
    print(f"\n🎉 Successfully reconstructed presentation: {output_pptx}")
    return output_pptx


if __name__ == "__main__":
    build_sample_presentation()
