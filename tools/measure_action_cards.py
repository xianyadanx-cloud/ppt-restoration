"""Measure exact pixel positions of action card boundaries in original Block 5."""
from PIL import Image

# Load the ORIGINAL input image (not diff)
img = Image.open("input/slide_02.png")
w, h = img.size
print(f"Original image size: {w}x{h}")

# Block 5 in original image spans x: 480..974 (normalized), y: 318..920 (normalized)
# Convert to actual pixels: canvas 1440x810
# x range: 480/1000 * 1440 = 691px to 974/1000 * 1440 = 1402px
# y range: 318/1000 * 810 = 257px to 920/1000 * 810 = 745px

# Sample at x=750 (inside the white card area of Block 5)
x_sample = 750
print(f"\nScanning x={x_sample} (inside Block 5 white area), y=350..700")
print("Looking for action card light-blue backgrounds vs white gaps...")

prev_tag = None
for y in range(350, 710):
    r, g, b = img.getpixel((x_sample, y))[:3]
    # Light blue card background: ~#EDF4FB = (237,244,251)
    is_card_bg = (r > 210 and g > 225 and b > 238 and r < 252 and not (r > 248 and g > 248))
    is_white = (r > 248 and g > 248 and b > 248)
    is_dark_blue = (r < 80 and b > 120)
    
    if is_dark_blue:
        tag = "DARK_BLUE"
    elif is_card_bg:
        tag = "CARD_BG"
    elif is_white:
        tag = "WHITE"
    else:
        tag = f"OTHER({r},{g},{b})"
    
    if tag != prev_tag or y % 10 == 0:
        print(f"  y={y:3d} (norm={y/810*1000:.0f}): RGB=({r:3d},{g:3d},{b:3d}) -> {tag}")
        prev_tag = tag
