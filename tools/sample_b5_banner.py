from PIL import Image
img = Image.open("input/slide_02.png").convert("RGB")
W, H = img.size
print(f"Image: {W}x{H}")

# Block5 banner 在原图的像素坐标
x1 = int(490/1000 * W)
y1 = int(325/1000 * H)
x2 = int((490+480)/1000 * W)
y2 = int((325+72)/1000 * H)
print(f"Block5 banner pixels: ({x1},{y1}) to ({x2},{y2})")

# 采样水平色带
for y in [y1+5, (y1+y2)//2, y2-5]:
    row = []
    for x in [x1+10, x1+80, (x1+x2)//2, x2-80, x2-10]:
        r, g, b = img.getpixel((x, y))[:3]
        row.append(f"#{r:02X}{g:02X}{b:02X}")
    print(f"  y={y} (norm={y/H*1000:.0f}): {' | '.join(row)}")
