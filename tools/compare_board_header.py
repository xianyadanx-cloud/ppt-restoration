"""High-resolution pixel-perfect crop comparison of Block 4."""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas, render_pptx_to_image

# 1. Render latest PPTX
render_pptx_to_image("output/slide_02.pptx", "output/sim_preview.png")

# 2. Load GT and Sim
raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
gt = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
sim = Image.open("output/sim_preview.png").convert("RGB")

# Crop Board Header (y: 240 to 440, x: 30 to 700)
gt_hdr = gt.crop((30, 240, 700, 440))
sim_hdr = sim.crop((30, 240, 700, 440))

# Create side by side
w, h = gt_hdr.size
comp = Image.new("RGB", (w * 2 + 20, h + 40), (15, 23, 42))
comp.paste(gt_hdr, (0, 40))
comp.paste(sim_hdr, (w + 20, 40))

draw = ImageDraw.Draw(comp)
draw.text((10, 10), "ORIGINAL Ground Truth (Header & Table Header)", fill=(56, 189, 248))
draw.text((w + 30, 10), "CURRENT RESTORED PPTX", fill=(74, 222, 128))

comp.save("output/debug_comp_header.png")
print("Saved output/debug_comp_header.png")

# Copy to brain dir
brain_dir = "/Users/feng.liu/.gemini/antigravity/brain/bfabae92-99cc-44f8-be22-fdbfd50d4e4c"
with open("output/debug_comp_header.png", "rb") as rf, open(f"{brain_dir}/debug_comp_header.png", "wb") as wf:
    wf.write(rf.read())
