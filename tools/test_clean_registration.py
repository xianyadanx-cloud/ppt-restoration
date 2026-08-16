"""Exact Canvas Registration & Block 5 Alignment Tool"""

import os
from PIL import Image, ImageDraw
from pptx import Presentation

# 1. Load raw original and sim preview
orig = Image.open("input/slide_02.png").convert("RGB").resize((1440, 810), Image.Resampling.LANCZOS)
sim = Image.open("output/sim_preview.png").convert("RGB").resize((1440, 810), Image.Resampling.LANCZOS)
p_orig = orig.load()

# In 1440x810 image:
# Find exact top edge of the "2+1" blue banner in orig
blue_banner_pts = [(x, y) for y in range(200, 400) for x in range(650, 1300) if p_orig[x, y][2] > 140 and p_orig[x, y][0] < 70 and p_orig[x, y][1] > 60]

min_y = min(pt[1] for pt in blue_banner_pts)
max_y = max(pt[1] for pt in blue_banner_pts)
min_x = min(pt[0] for pt in blue_banner_pts)
max_x = max(pt[0] for pt in blue_banner_pts)

print(f"Original '2+1' Banner in 1440x810: X=[{min_x}, {max_x}], Y=[{min_y}, {max_y}]")
print(f"Exact 0-1000 Coordinates: Left={min_x/1.44:.1f}, Top={min_y/0.81:.1f}, Width={(max_x-min_x)/1.44:.1f}, Height={(max_y-min_y)/0.81:.1f}")

# The true bottom of the Block 5 card in orig
# Footer pills end around Y=750 (0-1000: 925)
# So Block 5 bounding box in orig is:
# Left: min_x (approx 648 -> 450 in 0-1000)
# Top: min_y (approx 257 -> 317 in 0-1000)
# Right: 1390 (approx 965 in 0-1000)
# Bottom: 755 (approx 932 in 0-1000)

px_l = int(min_x - 10)
px_t = int(min_y) # EXACT TOP OF 2+1 BANNER
px_r = int(1400)
px_b = int(765)

crop_orig = orig.crop((px_l, px_t, px_r, px_b))
crop_sim = sim.crop((px_l, px_t, px_r, px_b))

# Create side-by-side diff
cw, ch = crop_orig.size
diff_img = Image.new("RGB", (cw * 2 + 20, ch + 50), (15, 23, 42))
diff_img.paste(crop_orig, (0, 50))
diff_img.paste(crop_sim, (cw + 20, 50))

draw = ImageDraw.Draw(diff_img)
draw.rectangle([10, 8, 300, 42], fill=(30, 41, 59))
draw.text((20, 16), "ORIGINAL [Exact Block 5 Crop]", fill=(56, 189, 248))
draw.rectangle([cw + 30, 8, cw + 360, 42], fill=(30, 41, 59))
draw.text((cw + 40, 16), "RESTORED [Exact Block 5 Crop]", fill=(74, 222, 128))

diff_img.save("output/diff_block5_pixel_perfect.png")
print("Successfully generated: output/diff_block5_pixel_perfect.png")
