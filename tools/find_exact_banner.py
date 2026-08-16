"""Find the exact banner of 2+1"""

from PIL import Image

orig = Image.open("input/slide_02.png").convert("RGB").resize((1440, 810), Image.Resampling.LANCZOS)
p = orig.load()

# The "2+1" text itself is pure white (R>240, G>240, B>240) in the banner
# Let's find white pixels surrounded by dark blue in y from 250 to 450, x from 600 to 800
t21_pts = []
for y in range(250, 450):
    for x in range(600, 800):
        r, g, b = p[x, y]
        if r > 240 and g > 240 and b > 240:
            # Check if 10 pixels above is blue
            if p[x, y - 10][2] > 130 and p[x, y - 10][0] < 80:
                t21_pts.append((x, y))

if t21_pts:
    min_21_y = min(pt[1] for pt in t21_pts)
    print(f"'2+1' white text top Y in 1440x810: {min_21_y}px (0-1000: {min_21_y/0.81:.1f})")
    
    # Now look upward from min_21_y to find the top edge of the blue banner
    banner_top_y = min_21_y
    for y in range(min_21_y, min_21_y - 80, -1):
        r, g, b = p[t21_pts[0][0], y]
        if b > 120 and r < 80:
            banner_top_y = y
        else:
            break
    print(f"Blue banner top edge Y in 1440x810: {banner_top_y}px (0-1000: {banner_top_y/0.81:.1f})")

    # Crop with banner_top_y as the exact top!
    crop_exact = orig.crop((650, banner_top_y, 1400, 765))
    crop_exact.save("output/exact_gt_b5_isolated.png")
    print(f"Saved output/exact_gt_b5_isolated.png with crop Y=[{banner_top_y}, 765]")
