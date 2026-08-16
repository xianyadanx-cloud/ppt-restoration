"""Inspect exact Y coordinates of all blocks in input/slide_02.png"""

import os
from PIL import Image

img = Image.open("input/slide_02.png").convert("RGB")
w, h = img.size
print(f"Original image size: {w}x{h}")
p = img.load()

# Let's find:
# 1. "季度工作攻坚策略" (Header)
# 2. "总览概述" (Summary banner)
# 3. "38万" (KPI)
# 4. "2+1" (Block 5)
# 5. "核心战役完成度全景" (Block 4)

def find_text_box(name, y_range, x_range, cond):
    pts = [(x, y) for y in range(y_range[0], y_range[1]) for x in range(x_range[0], x_range[1]) if cond(p[x, y])]
    if pts:
        min_x, max_x = min(pt[0] for pt in pts), max(pt[0] for pt in pts)
        min_y, max_y = min(pt[1] for pt in pts), max(pt[1] for pt in pts)
        print(f"[{name:<25}] Y: [{min_y:4d}, {max_y:4d}] (H={max_y-min_y:3d}px), X: [{min_x:4d}, {max_x:4d}] (W={max_x-min_x:3d}px) | Ratio: Y=[{min_y/h*1000:5.1f}, {max_y/h*1000:5.1f}], X=[{min_x/w*1000:5.1f}, {max_x/w*1000:5.1f}]")
        return (min_x, min_y, max_x, max_y)
    print(f"[{name:<25}] NOT FOUND")
    return None

print("-" * 90)
find_text_box("1. Main Title (季度工作...)", (0, 150), (0, 700), lambda c: c[0] < 50 and c[1] < 50 and c[2] < 50)
find_text_box("2. Summary Badge (总览概述)", (80, 200), (0, 300), lambda c: c[2] > 140 and c[0] < 60)
find_text_box("3. KPI 38万", (150, 300), (100, 600), lambda c: c[0] < 50 and c[1] < 50 and c[2] < 50)
find_text_box("4. Block 4 Header (核心战役...)", (250, 450), (0, 600), lambda c: c[0] < 50 and c[1] < 50 and c[2] < 50)
find_text_box("5. Block 5 Banner (2+1...)", (200, 400), (500, 1400), lambda c: c[2] > 140 and c[0] < 60 and c[1] > 60)
find_text_box("6. Block 5 Action 1 (流量重构)", (300, 550), (500, 1400), lambda c: c[0] < 50 and c[1] < 50 and c[2] < 50)
find_text_box("7. Block 5 Action 2 (触点再造)", (500, 750), (500, 1400), lambda c: c[0] < 50 and c[1] < 50 and c[2] < 50)
find_text_box("8. Block 5 Footer Pills", (650, 810), (500, 1400), lambda c: c[2] > 150 and c[0] < 60)
print("-" * 90)
