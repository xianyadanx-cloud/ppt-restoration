"""Find exact location of 2+1 in input/slide_02.png"""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
print(f"Raw image size: {raw.size}")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
print(f"Detected canvas: [{cl}, {ct}, {cr}, {cb}]")

canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
p = canvas.load()

# Let's find "2+1" text in canvas
# White text on blue banner: R>240, G>240, B>240 and adjacent pixels are blue (B>130, R<60)
pts = []
for y in range(0, 810):
    for x in range(0, 1440):
        r, g, b = p[x, y]
        # Dark blue banner
        if b > 140 and r < 70 and g > 60:
            pts.append((x, y))

# Find the blue banner for Block 5 (right half, x > 600)
b5_blue = [pt for pt in pts if pt[0] > 600]
if b5_blue:
    min_x = min(pt[0] for pt in b5_blue)
    max_x = max(pt[0] for pt in b5_blue)
    min_y = min(pt[1] for pt in b5_blue)
    max_y = max(pt[1] for pt in b5_blue)
    print(f"Block 5 Blue Banner in 1440x810: X=[{min_x}, {max_x}], Y=[{min_y}, {max_y}]")
    print(f"In 0-1000 scale: Top Y = {min_y / 810 * 1000:.1f}, Bottom Y = {max_y / 810 * 1000:.1f}")
    print(f"Left X = {min_x / 1440 * 1000:.1f}, Right X = {max_x / 1440 * 1000:.1f}")

    # Crop the exact Block 5
    crop_exact = canvas.crop((min_x - 10, min_y, max_x + 10, 800))
    crop_exact.save("output/exact_block5_gt.png")
    print("Saved output/exact_block5_gt.png")
