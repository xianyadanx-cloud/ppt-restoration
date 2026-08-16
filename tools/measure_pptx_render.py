"""Measure action card positions in the rendered PPTX sim preview."""
from PIL import Image

# Load the PPTX rendered preview
img = Image.open("output/sim_preview.png")
w, h = img.size
print(f"PPTX render size: {w}x{h}")

# Block 5 x range in normalized coords: 480..974
# Scan x=750 (center of Block 5)
x_sample = int(750 / 1000 * w)
print(f"\nScanning x={x_sample} (normalized=750), y for action card boundaries...")

prev_tag = None
for y in range(int(0.35 * h), int(0.80 * h)):
    r, g, b = img.getpixel((x_sample, y))[:3]
    is_card_bg = (r > 200 and g > 220 and b > 235 and r < 252 and not (r > 248 and g > 248))
    is_white = (r > 248 and g > 248 and b > 248)
    is_dark_blue = (r < 80 and b > 120)
    
    if is_dark_blue:
        tag = "DARK_BLUE"
    elif is_card_bg:
        tag = f"CARD_BG({r},{g},{b})"
    elif is_white:
        tag = "WHITE"
    else:
        tag = f"other({r},{g},{b})"
    
    norm_y = y / h * 1000
    if tag != prev_tag:
        print(f"  y={y:4d} (norm={norm_y:5.1f}): -> {tag}")
        prev_tag = tag
