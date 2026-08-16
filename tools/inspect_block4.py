"""Inspect Block 4 bounding box and sub-elements in input/slide_02.png."""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)

# Let's inspect the clipboard board location:
# Scan columns around x=100 from y=200 to 400 to find top blue edge of the clipboard
p = canvas.load()
for y in range(200, 350):
    r, g, b = p[100, y]
    # Clipboard blue color has high B, low R (e.g. R < 60, G > 80, B > 140)
    if b > 140 and r < 80:
        print(f"Clipboard top edge at y={y} px (normalized 0-1000: {y / 810.0 * 1000:.1f})")
        break

# Scan bottom edge of clipboard around x=100
for y in range(800, 600, -1):
    r, g, b = p[100, y]
    if b > 140 and r < 80:
        print(f"Clipboard bottom edge at y={y} px (normalized 0-1000: {y / 810.0 * 1000:.1f})")
        break

# Scan left edge of clipboard around y=500
for x in range(10, 200):
    r, g, b = p[x, 500]
    if b > 140 and r < 80:
        print(f"Clipboard left edge at x={x} px (normalized 0-1000: {x / 1440.0 * 1000:.1f})")
        break

# Scan right edge of clipboard around y=500
for x in range(700, 400, -1):
    r, g, b = p[x, 500]
    if b > 140 and r < 80:
        print(f"Clipboard right edge at x={x} px (normalized 0-1000: {x / 1440.0 * 1000:.1f})")
        break

# Table header location: scan column x=200 from top of clipboard
for y in range(250, 450):
    r, g, b = p[200, y]
    # Header is deep blue: R~30, G~100, B~180
    if b > 160 and r < 50 and g > 70:
        print(f"Table header top edge at y={y} px (normalized 0-1000: {y / 810.0 * 1000:.1f})")
        break

# Table header bottom
for y in range(300, 500):
    r, g, b = p[200, y]
    if (b > 160 and r < 50 and g > 70) and (p[200, y+2][2] < 150):
        print(f"Table header bottom edge at y={y} px (normalized 0-1000: {y / 810.0 * 1000:.1f})")
        break
