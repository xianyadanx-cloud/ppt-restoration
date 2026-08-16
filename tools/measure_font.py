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
    
    t_pts = []
    for y in range(120, 220):
        for x in range(50, 1300):
            r, g, b = p[x,y]
            if r < 80 and g < 80 and b < 80:
                t_pts.append((x,y))
                
    if t_pts:
        tx1 = min(pt[0] for pt in t_pts)
        tx2 = max(pt[0] for pt in t_pts)
        ty1 = min(pt[1] for pt in t_pts)
        ty2 = max(pt[1] for pt in t_pts)
        
        print(f"Ribbon text X px: {tx1} to {tx2} (Width: {tx2-tx1}px)")
        print(f"Ribbon text 0-1000 width: {(tx2-tx1)/1.44:.1f}")

if __name__ == "__main__":
    main()
