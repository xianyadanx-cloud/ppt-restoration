"""Ultra-precise crop of Block 4 table rows and columns to show exact alignment differences."""

import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import detect_inner_slide_canvas, render_pptx_to_image

render_pptx_to_image("output/slide_02.pptx", "output/sim_preview.png")

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
gt = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
sim = Image.open("output/sim_preview.png").convert("RGB")

# Crop the full Block 4 table area: x: 30 to 700, y: 220 to 780
gt_tbl = gt.crop((30, 220, 700, 780))
sim_tbl = sim.crop((30, 220, 700, 780))

w, h = gt_tbl.size
comp = Image.new("RGB", (w * 2 + 30, h + 50), (15, 23, 42))
comp.paste(gt_tbl, (0, 50))
comp.paste(sim_tbl, (w + 30, 50))

draw = ImageDraw.Draw(comp)
draw.rectangle([10, 10, w - 10, 42], fill=(30, 41, 59))
draw.text((20, 18), "1. ORIGINAL [Ground Truth Table & Alignment]", fill=(56, 189, 248))

draw.rectangle([w + 40, 10, w * 2 + 20, 42], fill=(30, 41, 59))
draw.text((w + 50, 18), "2. CURRENT RESTORED PPTX", fill=(244, 63, 94))

comp.save("output/debug_block4_full_table.png")
print("Saved output/debug_block4_full_table.png")

brain_dir = "/Users/feng.liu/.gemini/antigravity/brain/bfabae92-99cc-44f8-be22-fdbfd50d4e4c"
with open("output/debug_block4_full_table.png", "rb") as rf, open(f"{brain_dir}/debug_block4_full_table.png", "wb") as wf:
    wf.write(rf.read())
