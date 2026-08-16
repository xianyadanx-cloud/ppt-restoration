"""Generate a high-resolution 16:9 sample PPT slide image for demonstration."""

import os
from PIL import Image, ImageDraw, ImageFont


def create_sample_slide(output_path: str = "examples/sample_slide.png"):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), color=(248, 250, 252))  # #F8FAFC
    draw = ImageDraw.Draw(img)

    # 1. Header Area
    # Tag
    draw.rectangle([80, 60, 260, 95], fill=(219, 234, 254))  # Light blue tag
    draw.text((95, 70), "STRATEGY 2026", fill=(37, 99, 235))

    # Title & Subtitle
    draw.text((80, 110), "AI Agentic Automation Platform", fill=(15, 23, 42))
    draw.text((80, 150), "Driving operational excellence through native multimodal reconstruction", fill=(100, 116, 139))

    # Top-right Logo Badge (Simulated bitmap logo to test slicing)
    draw.ellipse([1720, 60, 1840, 180], fill=(37, 99, 235))
    draw.text((1755, 105), "LOGO", fill=(255, 255, 255))

    # 2. Card 1: Key Metrics & Narrative (Left)
    draw.rounded_rectangle([80, 220, 640, 920], radius=16, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((110, 250), "01 Core Capabilities", fill=(15, 23, 42))
    draw.text((110, 300), "Key strategic pillars for autonomous slide generation:", fill=(71, 85, 105))
    
    # Bullet points in Card 1
    bullets = [
        ("Native Reconstruction", "Generates true PowerPoint shapes, textframes, and tables."),
        ("Quality Gates", "Enforces strict style, blueprint, and typography checks."),
        ("Visual Verification", "Automates side-by-side diffing and inspection."),
        ("Zero API Bottleneck", "Runs directly on terminal with local python tools.")
    ]
    y_offset = 360
    for title, desc in bullets:
        draw.ellipse([110, y_offset + 5, 120, y_offset + 15], fill=(37, 99, 235))
        draw.text((135, y_offset), f"{title}:", fill=(30, 41, 59))
        draw.text((135, y_offset + 28), desc, fill=(100, 116, 139))
        y_offset += 75

    # Metric box inside Card 1
    draw.rounded_rectangle([110, 720, 610, 880], radius=12, fill=(238, 242, 255), outline=(199, 210, 254), width=1)
    draw.text((130, 740), "EFFICIENCY GAIN", fill=(79, 70, 229))
    draw.text((130, 770), "85% Faster Turnaround", fill=(30, 27, 75))
    draw.text((130, 830), "vs traditional manual PowerPoint drafting", fill=(100, 116, 139))

    # 3. Card 2: Performance Growth Chart (Middle)
    draw.rounded_rectangle([680, 220, 1240, 920], radius=16, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((710, 250), "02 Quarterly Performance", fill=(15, 23, 42))
    draw.text((710, 290), "Slide deck restoration volume by quarter (2026)", fill=(100, 116, 139))
    
    # Draw a simulated bar chart inside
    chart_x, chart_y, chart_w, chart_h = 740, 400, 440, 400
    draw.line([chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h], fill=(203, 213, 225), width=2)
    
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    vals = [120, 210, 340, 480]
    bar_w = 60
    for i, (q, v) in enumerate(zip(quarters, vals)):
        bx = chart_x + 30 + i * 105
        bh = int((v / 500.0) * 320)
        by = chart_y + chart_h - bh
        draw.rounded_rectangle([bx, by, bx + bar_w, chart_y + chart_h], radius=6, fill=(37, 99, 235))
        draw.text((bx + 15, by - 25), str(v), fill=(30, 41, 59))
        draw.text((bx + 18, chart_y + chart_h + 15), q, fill=(100, 116, 139))

    # 4. Card 3: Milestone Table (Right)
    draw.rounded_rectangle([1280, 220, 1840, 920], radius=16, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((1310, 250), "03 Execution Milestones", fill=(15, 23, 42))
    draw.text((1310, 290), "Tracked delivery stages & completion metrics", fill=(100, 116, 139))

    # Draw table
    tbl_x, tbl_y, tbl_w = 1310, 360, 500
    draw.rectangle([tbl_x, tbl_y, tbl_x + tbl_w, tbl_y + 45], fill=(15, 23, 42))
    draw.text((tbl_x + 20, tbl_y + 12), "Milestone", fill=(255, 255, 255))
    draw.text((tbl_x + 220, tbl_y + 12), "Owner", fill=(255, 255, 255))
    draw.text((tbl_x + 380, tbl_y + 12), "Status", fill=(255, 255, 255))

    rows = [
        ("M1 Blueprint", "Agent", "Done (100%)", (248, 250, 252)),
        ("M2 Native PPTX", "Agent", "Done (100%)", (255, 255, 255)),
        ("M3 Verification", "Verify.py", "Passed", (248, 250, 252)),
        ("M4 Multi-Merge", "Merge.py", "Ready", (255, 255, 255)),
        ("M5 Final Delivery", "Team", "Active", (248, 250, 252)),
    ]
    r_y = tbl_y + 45
    for m, o, s, bg in rows:
        draw.rectangle([tbl_x, r_y, tbl_x + tbl_w, r_y + 55], fill=bg, outline=(241, 245, 249))
        draw.text((tbl_x + 20, r_y + 15), m, fill=(30, 41, 59))
        draw.text((tbl_x + 220, r_y + 15), o, fill=(71, 85, 105))
        draw.text((tbl_x + 380, r_y + 15), s, fill=(16, 185, 129))
        r_y += 55

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path)
    print(f"[Success] Generated sample slide: {output_path}")


if __name__ == "__main__":
    create_sample_slide("examples/sample_slide.png")
    create_sample_slide("input/sample_slide.png")
