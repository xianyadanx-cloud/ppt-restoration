from PIL import Image
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from render_and_diff import detect_inner_slide_canvas

def main():
    raw = Image.open("input/slide_01.png").convert("RGB")
    cl, ct, cr, cb = detect_inner_slide_canvas(raw)
    canvas = raw.crop((cl, ct, cr, cb)).resize((1440, 810), Image.Resampling.LANCZOS)
    p = canvas.load()
    
    # Measure ribbon container (cyan/blue pixels around it)
    r_pts = []
    for y in range(100, 200):
        for x in range(30, 1300):
            r, g, b = p[x,y]
            if not (r > 240 and g > 240 and b > 240):  # Not white
                r_pts.append((x,y))
                
    if r_pts:
        rx1, ry1 = min(pt[0] for pt in r_pts), min(pt[1] for pt in r_pts)
        rx2, ry2 = max(pt[0] for pt in r_pts), max(pt[1] for pt in r_pts)
        print(f"Ribbon Area 0-1000: {rx1/1.44:.1f}, {ry1/0.81:.1f}, {(rx2-rx1)/1.44:.1f}, {(ry2-ry1)/0.81:.1f}")

if __name__ == "__main__":
    main()
