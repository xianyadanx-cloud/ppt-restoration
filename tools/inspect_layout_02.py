"""Accurately inspect layout of slide_02.png using only PIL."""

from PIL import Image

img = Image.open("input/slide_02.png").convert("RGB")
w, h = img.size
print(f"Image dimensions: {w} x {h}")

# Canvas background:
bg_sample = img.getpixel((20, 20))
print(f"Background sample at (20, 20): #{bg_sample[0]:02X}{bg_sample[1]:02X}{bg_sample[2]:02X}")

# Find top divider line:
# Look along vertical line at x = 700 (center of slide)
for y in range(80, 160):
    p = img.getpixel((700, y))
    # Check if gray/divider line
    if p[0] < 220 and p[1] < 220 and p[2] < 220:
        print(f"Divider line candidate at y={y} (norm_y={y/h*1000:.1f}): #{p[0]:02X}{p[1]:02X}{p[2]:02X}")

# Let's find horizontal span of divider line:
for y in [108, 109, 110, 111, 112, 113, 114, 115]:
    # scan x
    line_x = []
    for x in range(0, w):
        p = img.getpixel((x, y))
        if p[0] < 230 and p[1] < 230 and p[2] < 230 and abs(p[0]-p[1]) < 10:
            line_x.append(x)
    if len(line_x) > 500:
        print(f"Divider line at y={y}: x_min={min(line_x)} ({min(line_x)/w*1000:.1f}), x_max={max(line_x)} ({max(line_x)/w*1000:.1f})")

# Let's find top banner (总览概述)
# Badge on left: blue
# Scan for blue pixels (r < 70, g < 130, b > 160)
blue_pixels = []
for y in range(100, 300):
    for x in range(50, 300):
        r, g, b = img.getpixel((x, y))
        if r < 70 and g < 140 and b > 160:
            blue_pixels.append((x, y))

if blue_pixels:
    xs = [p[0] for p in blue_pixels]
    ys = [p[1] for p in blue_pixels]
    print(f"Top Summary Blue Badge: x=[{min(xs)}, {max(xs)}] (norm: [{min(xs)/w*1000:.1f}, {max(xs)/w*1000:.1f}]), y=[{min(ys)}, {max(ys)}] (norm: [{min(ys)/h*1000:.1f}, {max(ys)/h*1000:.1f}])")

# Top summary card right boundary:
# Scan along y=170 for card background:
for x in range(1200, 1400):
    r, g, b = img.getpixel((x, 175))
    if r < 245 or g < 245 or b < 245:
        # Check border
        pass

# Let's find the bottom section layout:
# Clipboard on the left, Strategy card on the right
# Blue strategy card (2+1 破局行动):
strat_blue = []
for y in range(300, 800):
    for x in range(650, 1400):
        r, g, b = img.getpixel((x, y))
        if r < 50 and 80 < g < 150 and b > 180:
            strat_blue.append((x, y))

if strat_blue:
    xs = [p[0] for p in strat_blue]
    ys = [p[1] for p in strat_blue]
    print(f"Right Strategy Blue Card: x=[{min(xs)}, {max(xs)}] (norm: [{min(xs)/w*1000:.1f}, {max(xs)/w*1000:.1f}]), y=[{min(ys)}, {max(ys)}] (norm: [{min(ys)/h*1000:.1f}, {max(ys)/h*1000:.1f}])")

# Clipboard baseplate on the left:
clip_blue = []
for y in range(300, 800):
    for x in range(50, 700):
        r, g, b = img.getpixel((x, y))
        if r < 50 and 80 < g < 150 and b > 180:
            clip_blue.append((x, y))

if clip_blue:
    xs = [p[0] for p in clip_blue]
    ys = [p[1] for p in clip_blue]
    print(f"Left Clipboard Blue Base: x=[{min(xs)}, {max(xs)}] (norm: [{min(xs)/w*1000:.1f}, {max(xs)/w*1000:.1f}]), y=[{min(ys)}, {max(ys)}] (norm: [{min(ys)/h*1000:.1f}, {max(ys)/h*1000:.1f}])")

# Top clip (metal) on clipboard:
metal_pixels = []
for y in range(300, 420):
    for x in range(200, 500):
        r, g, b = img.getpixel((x, y))
        # Gray metal (r~140..200, g~140..200, b~140..200, low saturation)
        if 100 < r < 210 and 100 < g < 210 and 100 < b < 210 and abs(r-g)<15 and abs(g-b)<15:
            metal_pixels.append((x, y))

if metal_pixels:
    xs = [p[0] for p in metal_pixels]
    ys = [p[1] for p in metal_pixels]
    print(f"Top Metallic Clip: x=[{min(xs)}, {max(xs)}] (norm: [{min(xs)/w*1000:.1f}, {max(xs)/w*1000:.1f}]), y=[{min(ys)}, {max(ys)}] (norm: [{min(ys)/h*1000:.1f}, {max(ys)/h*1000:.1f}])")
