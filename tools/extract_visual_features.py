"""Visual Feature Extraction & Pixel-Accurate Profiling Tool

Samples exact colors, gradient ramps, polygon vertices, bounding boxes,
and font size heights (pt) directly from input/slide_01.png.
"""

from PIL import Image, ImageStat


def get_rgb(img, x, y):
    r, g, b = img.getpixel((int(x), int(y)))[:3]
    return f"#{r:02X}{g:02X}{b:02X}", (r, g, b)


def get_region_avg_rgb(img, box):
    crop = img.crop(box)
    stat = ImageStat.Stat(crop)
    r, g, b = [int(v) for v in stat.mean[:3]]
    return f"#{r:02X}{g:02X}{b:02X}", (r, g, b)


def run_visual_profile():
    img = Image.open("input/slide_01.png").convert("RGB")
    w, h = img.size
    print(f"Image Resolution: {w}x{h} (Aspect Ratio: {w/h:.3f})")
    print("=" * 60)
    print("🎨 1. EXACT COLOR PROBING (RGB & HEX)")
    print("=" * 60)

    probes = {
        "Slide Canvas Background": (50, 50),
        "Top Header Text '问题分析与解决路径'": (120, 75),
        "Top Header Divider Line": (300, 96),
        "Quote Banner Background": (400, 140),
        "Quote Banner Border": (400, 126),
        "Quote Banner Wing Light Blue": (70, 142),
        "Left 3D Top Extruded Slope (Top)": (200, 248),
        "Left 3D Top Extruded Slope (Bottom)": (200, 280),
        "Left 3D Spine Thickness Edge": (85, 450),
        "Left 3D Front Panel (Top)": (250, 310),
        "Left 3D Front Panel (Bottom)": (250, 740),
        "Left Card Pill Badge Fill": (170, 320),
        "Left Sub-banner Fill": (300, 275),
        "Left Card White Background": (300, 380),
        "Left Card Metric Cyan Highlight (60%)": (280, 355),
        "Left Card Metric Red Highlight (低于保本线)": (430, 355),
        "Right 3D Top Extruded Slope (Top)": (1000, 248),
        "Right 3D Top Extruded Slope (Bottom)": (1000, 280),
        "Right 3D Spine Thickness Edge": (1280, 450),
        "Right 3D Front Panel (Top)": (1000, 310),
        "Right 3D Front Panel (Bottom)": (1000, 740),
        "Right Card Pill Badge Fill": (1180, 320),
        "Right Sub-banner Fill": (1000, 275),
        "Right Card White Background": (1000, 380),
        "Right Card Metric Red Highlight (5大作战网格)": (830, 355),
        "Right Card Metric Green Highlight (提升至85%)": (1150, 375),
        "Center Poju Calligraphy Text": (650, 185),
        "Center 3D Glass Sphere Body": (715, 195),
        "Center 3D Glass Sphere Highlight": (705, 188),
        "Center Binder Ring Outer Metal": (690, 410),
        "Center Spine Cleft Shadow": (690, 500),
    }

    for name, (px, py) in probes.items():
        hex_val, (r, g, b) = get_rgb(img, px, py)
        norm_x = round(px / w * 1000, 1)
        norm_y = round(py / h * 1000, 1)
        print(f"  • {name:<46}: {hex_val} (rgb: {r:3d}, {g:3d}, {b:3d}) @ [{norm_x:5.1f}, {norm_y:5.1f}]")

    print("\n" + "=" * 60)
    print("📐 2. EXACT SHAPE BOUNDS & VERTICES (0-1000 Coordinates)")
    print("=" * 60)

    # 1 px in 810 height = 0.667 pt
    px_to_pt = 72.0 * 7.5 / 810.0  # 0.66667 pt per pixel

    print(f"Scale Conversion: 1 px height = {px_to_pt:.4f} pt in PowerPoint")

    regions = {
        "Main Title Box": (60, 40, 550, 50),
        "Quote Ribbon Banner": (95, 115, 1250, 50),
        "3D Left Top Slope": (75, 230, 615, 60),
        "3D Right Top Slope": (690, 230, 615, 60),
        "Left Card 1": (120, 295, 520, 120),
        "Left Card 2": (120, 425, 520, 120),
        "Left Card 3": (120, 555, 520, 120),
        "Right Card 1": (740, 295, 520, 120),
        "Right Card 2": (740, 425, 520, 120),
        "Right Card 3": (740, 555, 520, 120),
        "Center Binder Rings": (675, 290, 30, 450),
    }

    for name, (rx, ry, rw, rh) in regions.items():
        norm_x = rx / w * 1000
        norm_y = ry / h * 1000
        norm_w = rw / w * 1000
        norm_h = rh / h * 1000
        h_pt = rh * px_to_pt
        print(f"  • {name:<25}: box=[{norm_x:5.1f}, {norm_y:5.1f}, {norm_w:5.1f}, {norm_h:5.1f}] -> height={h_pt:.1f}pt")


if __name__ == "__main__":
    run_visual_profile()
