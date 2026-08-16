"""Check canvas detection and exact coordinates of Block 5 in input/slide_02.png."""
import os, sys
sys.path.insert(0, os.path.abspath("."))
from PIL import Image
from tools.render_and_diff import detect_inner_slide_canvas

raw = Image.open("input/slide_02.png").convert("RGB")
cl, ct, cr, cb = detect_inner_slide_canvas(raw)
print(f"Raw image size: {raw.size}")
print(f"Detected inner canvas bbox: ({cl}, {ct}, {cr}, {cb}) -> size: ({cr-cl}, {cb-ct})")

cropped = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.LANCZOS)
cropped.save("output/debug_cropped_orig_canvas.png")

# Now sample Block 5 top banner on this normalized (1440x810) canvas
# box: [480, 318, 494, 82]
# in pixels on 1440x810:
# left = 480/1000*1440 = 691
# top = 318/1000*810 = 257
# right = (480+494)/1000*1440 = 1402
# bottom = (318+82)/1000*810 = 324

print("Sampling normalized cropped canvas at Block 5 banner:")
for y_norm in [330, 350, 370]:
    row = []
    for x_norm in [500, 600, 700, 800, 900]:
        px_x = int(x_norm / 1000.0 * 1440)
        px_y = int(y_norm / 1000.0 * 810)
        r, g, b = cropped.getpixel((px_x, px_y))[:3]
        row.append(f"({x_norm},{y_norm}): #{r:02X}{g:02X}{b:02X}")
    print("  " + " | ".join(row))
