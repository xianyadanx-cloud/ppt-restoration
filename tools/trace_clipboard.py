"""Find vertical layout of clipboard."""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
p = canvas.load()

# Let's inspect column x=100 from y=250 to 780
for y in range(250, 780, 5):
    r, g, b = p[100, y]
    # Check if white, blue, or pink
    color_type = "WHITE"
    if b > 140 and r < 80:
        color_type = f"BLUE ({r},{g},{b})"
    elif r > 240 and g > 230 and b > 230:
        color_type = f"WHITE ({r},{g},{b})"
    elif r > 240 and g < 240 and b < 240:
        color_type = f"PINK ({r},{g},{b})"
    print(f"y={y:3d} (0-1000: {y/810.0*1000:5.1f}) -> {color_type}")
