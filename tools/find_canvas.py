"""Find the actual slide canvas bounds inside input/slide_02.png."""

from PIL import Image

img = Image.open("input/slide_02.png").convert("RGB")
w, h = img.size

# Let's find the bounding box of the white slide canvas if there is an outer border/shadow
# Scan from edges inwards to find where the white background starts:
# Top edge:
top_edge = 0
for y in range(0, h // 2):
    row_pixels = [img.getpixel((x, y)) for x in range(w // 4, 3 * w // 4)]
    avg_val = sum(p[0] + p[1] + p[2] for p in row_pixels) / (3 * len(row_pixels))
    if avg_val > 240:
        top_edge = y
        break

# Bottom edge:
bottom_edge = h - 1
for y in range(h - 1, h // 2, -1):
    row_pixels = [img.getpixel((x, y)) for x in range(w // 4, 3 * w // 4)]
    avg_val = sum(p[0] + p[1] + p[2] for p in row_pixels) / (3 * len(row_pixels))
    if avg_val > 240:
        bottom_edge = y
        break

# Left edge:
left_edge = 0
for x in range(0, w // 2):
    col_pixels = [img.getpixel((x, y)) for y in range(h // 4, 3 * h // 4)]
    avg_val = sum(p[0] + p[1] + p[2] for p in col_pixels) / (3 * len(col_pixels))
    if avg_val > 240:
        left_edge = x
        break

# Right edge:
right_edge = w - 1
for x in range(w - 1, w // 2, -1):
    col_pixels = [img.getpixel((x, y)) for y in range(h // 4, 3 * h // 4)]
    avg_val = sum(p[0] + p[1] + p[2] for p in col_pixels) / (3 * len(col_pixels))
    if avg_val > 240:
        right_edge = x
        break

print(f"Slide Canvas Bounding Box in image: [{left_edge}, {top_edge}, {right_edge}, {bottom_edge}]")
print(f"Slide Canvas Size: {right_edge - left_edge + 1} x {bottom_edge - top_edge + 1}")
print(f"Aspect ratio: {(right_edge - left_edge + 1) / (bottom_edge - top_edge + 1):.3f}")
