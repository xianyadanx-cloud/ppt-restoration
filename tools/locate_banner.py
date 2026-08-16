"""Locate Block 5 banner on the cropped canvas."""
from PIL import Image

img = Image.open("output/debug_cropped_orig_canvas.png")
w, h = img.size
print(f"Canvas size: {w}x{h}")

# Search for the blue banner text "2+1" or blue pixels (R < 50, B > 150)
print("Scanning for blue banner pixels in X=500..1400, Y=100..700:")
found_y = []
for y in range(100, 700, 5):
    for x in range(700, 1400, 10):
        r, g, b = img.getpixel((x, y))[:3]
        if r < 60 and g > 80 and b > 160:
            found_y.append(y)
            break

if found_y:
    min_y, max_y = min(found_y), max(found_y)
    print(f"Blue banner Y span in pixels: {min_y}..{max_y}")
    print(f"Normalized Y span (0-1000): {min_y/h*1000:.0f} .. {max_y/h*1000:.0f}")

# Sample banner colors across width at mid-Y
if found_y:
    sample_y = (min_y + max_y) // 2
    print(f"\nSampling banner horizontal colors at Y={sample_y} (norm={sample_y/h*1000:.0f}):")
    for x_norm in [520, 600, 700, 800, 900, 960]:
        px_x = int(x_norm / 1000.0 * w)
        r, g, b = img.getpixel((px_x, sample_y))[:3]
        print(f"  X={x_norm}: #{r:02X}{g:02X}{b:02X}")
