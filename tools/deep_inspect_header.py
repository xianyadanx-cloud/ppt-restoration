"""Deep inspect 核心战役完成度全景 and blue table header in input/slide_02.png."""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

# 1. Crop Title area in canvas: around x: 50~700, y: 250~350
title_crop = canvas.crop((40, 240, 680, 360))
title_crop.save("output/crop_gt_title.png")

# 2. Crop Table header area: around x: 40~680, y: 320~400
header_crop = canvas.crop((40, 310, 680, 410))
header_crop.save("output/crop_gt_header.png")

print(f"Canvas size: {canvas.size}")
# Let's find the exact horizontal bounding box of the black text "核心战役完成度全景"
p = canvas.load()
text_pixels = []
for y in range(260, 350):
    for x in range(50, 650):
        r, g, b = p[x, y]
        # Text is black/dark gray (R < 60, G < 60, B < 60)
        if r < 60 and g < 60 and b < 60:
            text_pixels.append((x, y))

if text_pixels:
    min_x = min(pt[0] for pt in text_pixels)
    max_x = max(pt[0] for pt in text_pixels)
    min_y = min(pt[1] for pt in text_pixels)
    max_y = max(pt[1] for pt in text_pixels)
    h_px = max_y - min_y
    w_px = max_x - min_x
    print(f"[GT Title] Bounding box in 1440x810: X=[{min_x}, {max_x}] (W={w_px}), Y=[{min_y}, {max_y}] (H={h_px})")
    print(f"[GT Title] Center X: {(min_x + max_x) / 2:.1f} (in 0-1000: {((min_x + max_x) / 2) / 1440 * 1000:.1f})")
    print(f"[GT Title] In 0-1000 scale: box=[{min_x/1.44:.1f}, {min_y/0.81:.1f}, {w_px/1.44:.1f}, {h_px/0.81:.1f}]")
    print(f"[GT Title] Font physical height: {h_px} px -> approx {h_px * 0.667:.1f} pt")

# Let's inspect the clipboard white paper horizontal bounds at y=300
paper_x = []
for x in range(30, 700):
    r, g, b = p[x, 300]
    if r > 240 and g > 240 and b > 240:
        paper_x.append(x)
if paper_x:
    paper_min = min(paper_x)
    paper_max = max(paper_x)
    print(f"[Paper X] [{paper_min}, {paper_max}] (Center X: {(paper_min+paper_max)/2:.1f} -> 0-1000: {((paper_min+paper_max)/2)/1.44:.1f})")

# Let's inspect the blue table header gradient colors
# Header is around y=330~380
header_blue_px = []
for y in range(310, 400):
    for x in range(50, 650):
        r, g, b = p[x, y]
        if b > 140 and r < 80 and g > 60:
            header_blue_px.append((x, y, (r, g, b)))

if header_blue_px:
    min_hy = min(pt[1] for pt in header_blue_px)
    max_hy = max(pt[1] for pt in header_blue_px)
    min_hx = min(pt[0] for pt in header_blue_px)
    max_hx = max(pt[0] for pt in header_blue_px)
    print(f"[Header Blue] Bounding box: X=[{min_hx}, {max_hx}], Y=[{min_hy}, {max_hy}]")
    # Top color vs bottom color of the header bar
    top_colors = [pt[2] for pt in header_blue_px if pt[1] == min_hy + 2]
    bot_colors = [pt[2] for pt in header_blue_px if pt[1] == max_hy - 2]
    if top_colors:
        avg_top = tuple(sum(c[i] for c in top_colors)//len(top_colors) for i in range(3))
        print(f"[Header Top Color] RGB={avg_top}, Hex=#{avg_top[0]:02X}{avg_top[1]:02X}{avg_top[2]:02X}")
    if bot_colors:
        avg_bot = tuple(sum(c[i] for c in bot_colors)//len(bot_colors) for i in range(3))
        print(f"[Header Bottom Color] RGB={avg_bot}, Hex=#{avg_bot[0]:02X}{avg_bot[1]:02X}{avg_bot[2]:02X}")
