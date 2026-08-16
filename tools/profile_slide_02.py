"""Visual Profiler specifically for input/slide_02.png."""

import os
from PIL import Image, ImageStat


def get_rgb(img, x, y):
    r, g, b = img.getpixel((int(x), int(y)))[:3]
    return f"#{r:02X}{g:02X}{b:02X}", (r, g, b)


def get_region_avg_rgb(img, box):
    crop = img.crop(box)
    stat = ImageStat.Stat(crop)
    r, g, b = [int(v) for v in stat.mean[:3]]
    return f"#{r:02X}{g:02X}{b:02X}", (r, g, b)


def profile_slide_02():
    img = Image.open("input/slide_02.png").convert("RGB")
    w, h = img.size
    print(f"Slide 02 Image Resolution: {w}x{h} (Aspect Ratio: {w/h:.3f})")
    print("=" * 65)
    print("🎨 1. EXACT COLOR PROBES FOR SLIDE 02")
    print("=" * 65)

    probes = {
        "Main Canvas Background (top-left)": (50, 50),
        "Main Title Text '季度工作攻坚策略'": (150, 95),
        "Header Divider Line": (200, 140),
        "Author Tag '@鱼丸PPT'": (870, 95),
        "Top Summary Badge Fill (总览概述)": (100, 210),
        "Top Summary Card Background": (250, 210),
        "Middle Subtitle '多维度运营效能透视'": (150, 320),
        "KPI 1 Top Tag Fill (规模缺口)": (565, 322),
        "KPI 1 Main Value '38万'": (565, 370),
        "KPI 1 Bottom Badge Fill (缺口16%)": (565, 415),
        "KPI Arrow 1 Circle Fill": (650, 375),
        "KPI 2 Top Tag Fill (转化迟滞)": (735, 322),
        "KPI 2 Main Value '6.1%'": (735, 370),
        "KPI 2 Bottom Badge Fill (缺口0.4pp)": (735, 415),
        "KPI Arrow 2 Circle Fill": (820, 375),
        "KPI 3 Top Tag Fill (成本刚性)": (905, 322),
        "KPI 3 Main Value '9%降幅'": (905, 370),
        "KPI 3 Bottom Badge Fill (缺口6pp)": (905, 415),
        "Left Clipboard Base Plate Deep Blue": (80, 500),
        "Left Paper White Sheet": (200, 500),
        "Left Metallic Clip Top": (270, 442),
        "Left Table Header Blue Fill": (200, 545),
        "Left Table Alt Row Fill": (200, 650),
        "Progress Bar Fill (Orange)": (370, 608),
        "Progress Bar Track (Peach)": (410, 608),
        "Right Big Blue Card Body": (600, 500),
        "Right '2+1' Giant Text": (525, 495),
        "Right '破局行动' Title": (615, 505),
        "Right Ribbon Quote Pill Fill": (750, 505),
        "Right White Action Card 1 Fill": (600, 600),
        "Right Badge '1' Fill": (515, 580),
        "Right White Action Card 2 Fill": (600, 750),
        "Right Badge '2' Fill": (515, 720),
        "Right Bottom Long Pill Badge Fill": (560, 865),
        "Right Bottom White Keyword Pill": (670, 865),
    }

    for name, (px, py) in probes.items():
        if px < w and py < h:
            hex_val, (r, g, b) = get_rgb(img, px, py)
            norm_x = round(px / w * 1000, 1)
            norm_y = round(py / h * 1000, 1)
            print(f"  • {name:<42}: {hex_val} (rgb: {r:3d}, {g:3d}, {b:3d}) @ [{norm_x:5.1f}, {norm_y:5.1f}]")

    print("\n" + "=" * 65)
    print("📐 2. BOUNDING BOXES & MACRO BLUEPRINT (0-1000 Scale)")
    print("=" * 65)

    regions = {
        "Main Title Header": (70, 65, 400, 50),
        "Author Tag": (800, 75, 120, 35),
        "Header Divider Line": (70, 138, 850, 2),
        "Top Summary Card": (70, 165, 860, 100),
        "Top Summary Blue Badge": (70, 165, 85, 100),
        "Middle Subtitle Area": (70, 300, 420, 110),
        "KPI Card 1 (规模缺口)": (515, 305, 95, 125),
        "KPI Arrow 1": (640, 360, 20, 20),
        "KPI Card 2 (转化迟滞)": (685, 305, 95, 125),
        "KPI Arrow 2": (810, 360, 20, 20),
        "KPI Card 3 (成本刚性)": (855, 305, 95, 125),
        "Left Clipboard Baseplate": (70, 440, 415, 475),
        "Left Paper Sheet": (80, 452, 395, 450),
        "Left Top Metallic Clip": (230, 435, 95, 22),
        "Left Table Box": (90, 515, 375, 365),
        "Right Strategy Big Blue Card": (500, 450, 430, 435),
        "Right Strategy Header (2+1)": (500, 460, 430, 40),
        "Right Action Card 1": (515, 550, 400, 135),
        "Right Action Card 2": (515, 700, 400, 135),
        "Right Bottom Pills Row": (515, 850, 400, 28),
    }

    for name, (rx, ry, rw, rh) in regions.items():
        norm_x = round(rx / w * 1000, 1)
        norm_y = round(ry / h * 1000, 1)
        norm_w = round(rw / w * 1000, 1)
        norm_h = round(rh / h * 1000, 1)
        print(f"  • {name:<30}: box=[{norm_x:5.1f}, {norm_y:5.1f}, {norm_w:5.1f}, {norm_h:5.1f}]")


if __name__ == "__main__":
    profile_slide_02()
