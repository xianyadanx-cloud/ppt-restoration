"""Task Scaffold Generator for Multi-Slide Decks.

Scans the input/ directory, inspects slide image dimensions, and initializes
skeleton slide construction scripts under slides/ for the Coding Agent to build.
"""

import os
import glob
import argparse


SKELETON_TEMPLATE = '''"""Slide Construction Script for {slide_name}

Auto-generated scaffold. Follow AGENTS.md SOP:
1. Macro Blueprint Gate: Plan [left, top, width, height] for each block.
2. Slicing: Crop any bitmap images using tools/slice.py if needed.
3. Native Elements: Build header, cards, native charts, tables, and typography.
4. Verify: Run `python tools/verify.py {input_path} output/{slide_name}.pptx`
"""

import os
import sys

# Ensure tools package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.pptx_helper import SlideBuilder


def build_slide():
    # 1. Initialize builder from source image (auto-detects 16:9 / 4:3)
    builder = SlideBuilder.from_image("{input_path}", bg_color="#F8FAFC")

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
            {{"text": "01 Key Pillar\\n", "size": 15, "bold": True, "color": "#0F172A"}},
            {{"text": "Add descriptive details, metrics, and structured insights here.\\n\\n", "size": 11, "color": "#475569"}},
        ]
    )

    # Example Chart / Table or Second Card
    builder.add_card(box=[520, 160, 440, 520], bg_color="#FFFFFF", border_color="#E2E8F0", radius=True)
    builder.add_chart(
        box=[540, 180, 400, 480],
        chart_type="column",
        categories=["Q1", "Q2", "Q3", "Q4"],
        series=[{{"name": "Performance", "values": [45, 68, 85, 110]}}],
        title="Performance Trend",
    )

    # 4. Save PPTX
    output_path = "output/{slide_name}.pptx"
    builder.save(output_path)
    return output_path


if __name__ == "__main__":
    build_slide()
'''


def init_deck(input_dir: str = "input", slides_dir: str = "slides"):
    os.makedirs(slides_dir, exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("assets", exist_ok=True)

    image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp")
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_dir, ext)))

    image_files = sorted(image_files)

    if not image_files:
        print(f"[Notice] No images found in {input_dir}/. Place your slide images or PDF there.")
        return

    print(f"🚀 Initializing task scaffold for {len(image_files)} slides found in {input_dir}/...\n")

    created = 0
    for img_path in image_files:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        script_name = f"build_{base_name}.py"
        script_path = os.path.join(slides_dir, script_name)

        if not os.path.exists(script_path):
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(SKELETON_TEMPLATE.format(slide_name=base_name, input_path=img_path))
            print(f"  [+] Created scaffold: {script_path}")
            created += 1
        else:
            print(f"  [.] Already exists: {script_path}")

    print(f"\n✨ Initialization complete! {created} new slide scripts created in {slides_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Initialize slide construction script scaffolds.")
    parser.add_argument("--input-dir", default="input", help="Directory with input slide images")
    parser.add_argument("--slides-dir", default="slides", help="Directory for generated scripts")
    args = parser.parse_args()

    init_deck(args.input_dir, args.slides_dir)


if __name__ == "__main__":
    main()
