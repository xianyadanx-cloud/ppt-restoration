"""Verify PingFang TTC font indices and gradient rendering."""

import os
from PIL import Image, ImageDraw, ImageFont

font_paths = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
]

for idx in range(6):
    try:
        f = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24, index=idx)
        img = Image.new("RGB", (300, 50), (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"Index {idx}: 核心战役完成度", fill=(0, 0, 0), font=f)
        img.save(f"output/font_idx_{idx}.png")
        print(f"Index {idx} name: {f.font.family} - {f.font.style}")
    except Exception as e:
        print(f"Index {idx} error: {e}")
