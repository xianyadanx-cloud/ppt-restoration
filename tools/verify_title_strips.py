"""Sample pixel colors in Action 1: title row vs bullet lines in GT image."""
from PIL import Image

gt = Image.open("output/exact_gt_b5_isolated.png").convert("RGB")
w, h = gt.size
print(f"GT image size: {w}x{h}")

# Action 1 title row is around y=90..130 (in the crop)
# Action 1 bullets are around y=140..200
# Action 2 title row is around y=230..270
# Action 2 bullets are around y=280..340

print("Sampling vertical column at x=200 (behind title text and bullets):")
for y in range(80, 360, 10):
    r, g, b = gt.getpixel((200, y))[:3]
    # Classify
    tag = "WHITE" if (r > 248 and g > 248 and b > 248) else ("LIGHT_BLUE_BANNER" if (r > 210 and g > 225 and b > 240) else f"RGB({r},{g},{b})")
    print(f"  y={y:3d}: RGB=({r:3d},{g:3d},{b:3d}) -> {tag}")
