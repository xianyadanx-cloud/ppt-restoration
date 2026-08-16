"""Generate visual block segmentation map and slice diffs for all blocks."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image, ImageDraw, ImageFont
from tools.render_and_diff import render_pptx_to_image, compare_and_generate_diff, detect_inner_slide_canvas

# 1. Load clean slide canvas
raw_img = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw_img)
canvas = raw_img.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

# Create Block Annotation Map
annotated = canvas.copy().convert("RGBA")
overlay = Image.new("RGBA", (1440, 810), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# Font setup with Chinese fallback
font_paths = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]
fnt_title = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            fnt_title = ImageFont.truetype(fp, 18, index=0)
            break
        except Exception:
            try:
                fnt_title = ImageFont.truetype(fp, 18)
                break
            except Exception:
                pass

if not fnt_title:
    fnt_title = ImageFont.load_default()

blocks = [
    {
        "id": "Block 1",
        "name": "顶部主标题区 (Header)",
        "box": [30, 25, 940, 72],
        "color": (29, 78, 216),  # Royal Blue
        "func": "add_header_section",
    },
    {
        "id": "Block 2",
        "name": "总结概览横幅 (Summary Banner)",
        "box": [30, 105, 940, 78],
        "color": (5, 150, 105),  # Emerald Green
        "func": "add_summary_banner_section",
    },
    {
        "id": "Block 3",
        "name": "效能透视与 KPI 组 (Mid KPIs)",
        "box": [30, 192, 940, 115],
        "color": (217, 119, 6),  # Amber
        "func": "add_mid_kpi_section",
    },
    {
        "id": "Block 4",
        "name": "拟物战役板夹 (Clipboard Table)",
        "box": [30, 318, 438, 602],
        "color": (124, 58, 237),  # Purple
        "func": "add_clipboard_table_section",
    },
    {
        "id": "Block 5",
        "name": "2+1 破局行动大卡 (Strategy Card)",
        "box": [480, 318, 490, 602],
        "color": (225, 29, 72),  # Rose Red
        "func": "add_strategy_card_section",
    },
]

w, h = 1440, 810

for b in blocks:
    l, t, bw, bh = b["box"]
    px_l = int(l / 1000.0 * w)
    px_t = int(t / 1000.0 * h)
    px_r = int((l + bw) / 1000.0 * w)
    px_b = int((t + bh) / 1000.0 * h)

    c = b["color"]
    fill_c = (c[0], c[1], c[2], 30)
    border_c = (c[0], c[1], c[2], 235)

    # Draw rounded rectangle outline
    draw.rounded_rectangle([px_l, px_t, px_r, px_b], radius=8, fill=fill_c, outline=border_c, width=3)

    # Draw solid label badge
    lbl_text = f" {b['id']}: {b['name']} "
    bbox = draw.textbbox((0, 0), lbl_text, font=fnt_title)
    lbl_w = bbox[2] - bbox[0] + 16
    lbl_h = 28

    badge_top = max(4, px_t - 14 if px_t > 24 else px_t + 4)
    badge_left = px_l + 8

    draw.rounded_rectangle([badge_left, badge_top, badge_left + lbl_w, badge_top + lbl_h], radius=5, fill=(c[0], c[1], c[2], 245))
    draw.text((badge_left + 8, badge_top + 4), lbl_text, fill=(255, 255, 255, 255), font=fnt_title)

annotated = Image.alpha_composite(annotated, overlay).convert("RGB")
os.makedirs("output", exist_ok=True)
annotated.save("output/block_layout_map.png")
print("[Success] Generated visual block segmentation map: output/block_layout_map.png")

# 2. Render all block slice diffs
pptx_path = "output/slide_02.pptx"
sim_path = "output/sim_preview.png"
render_pptx_to_image(pptx_path, sim_path)

slice_configs = [
    ("Block 1 [Header]", [30, 20, 940, 85], "output/diff_block_01_header.png"),
    ("Block 2 [Summary]", [30, 95, 940, 95], "output/diff_block_02_summary.png"),
    ("Block 3 [KPIs]", [30, 180, 940, 135], "output/diff_block_03_kpi.png"),
    ("Block 4 [Clipboard Table]", [30, 310, 445, 630], "output/diff_block_04_clipboard.png"),
    ("Block 5 [Strategy Card]", [475, 310, 500, 630], "output/diff_block_05_strategy.png"),
]

for title, box, out_p in slice_configs:
    compare_and_generate_diff("input/slide_02.png", sim_path, out_p, crop_box=box, block_title=title)

# Copy artifacts to brain directory
brain_dir = "/Users/feng.liu/.gemini/antigravity/brain/bfabae92-99cc-44f8-be22-fdbfd50d4e4c"
for f in ["block_layout_map.png", "diff_block_01_header.png", "diff_block_02_summary.png", "diff_block_03_kpi.png", "diff_block_04_clipboard.png", "diff_block_05_strategy.png"]:
    src = f"output/{f}"
    dst = f"{brain_dir}/{f}"
    if os.path.exists(src):
        with open(src, "rb") as rf, open(dst, "wb") as wf:
            wf.write(rf.read())
print(f"[Success] Copied all block artifacts to {brain_dir}")
