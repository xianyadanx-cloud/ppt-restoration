"""Slice slide_02 into detailed visual strips for inspection."""

import os
from PIL import Image

img = Image.open("input/slide_02.png")
w, h = img.size

# Let's crop the actual slide canvas from input/slide_02.png:
# In input/slide_02.png:
# Slide canvas is within [70, 37, 1370, 767]
# Let's crop the slide canvas and save it
canvas_crop = img.crop((70, 37, 1370, 767))
os.makedirs("output/inspect", exist_ok=True)
canvas_crop.save("output/inspect/canvas_slide_02.png")

cw, ch = canvas_crop.size
print(f"Canvas size: {cw} x {ch}")

# Let's slice key sections from the cropped canvas (in 0-1000 scale relative to canvas):
def slice_canvas(box, name):
    l, t, rw, rh = box
    px_l = int(l / 1000.0 * cw)
    px_t = int(t / 1000.0 * ch)
    px_r = int((l + rw) / 1000.0 * cw)
    px_b = int((t + rh) / 1000.0 * ch)
    cropped = canvas_crop.crop((px_l, px_t, px_r, px_b))
    cropped.save(f"output/inspect/{name}.png")
    print(f"Saved {name}.png: [{l}, {t}, {rw}, {rh}] -> {cropped.size}")

slice_canvas([0, 0, 1000, 150], "01_header")
slice_canvas([0, 120, 1000, 160], "02_summary_banner")
slice_canvas([0, 260, 500, 180], "03_mid_title_desc")
slice_canvas([480, 260, 520, 180], "04_kpi_cards")
slice_canvas([0, 420, 510, 580], "05_bottom_left_clipboard")
slice_canvas([490, 420, 510, 580], "06_bottom_right_strategy")
