"""Crop table header and title from canvas."""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

# Crop from y=340 to y=520, x=30 to x=680
crop = canvas.crop((30, 330, 680, 520))
crop.save("output/crop_board_header.png")
print("Saved output/crop_board_header.png")
