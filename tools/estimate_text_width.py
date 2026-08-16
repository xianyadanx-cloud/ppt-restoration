"""Estimate how many chars fit in a textbox at given font size."""

# The render canvas is 1440x810, corresponding to normalized 0-1000
# So width=455 normalized = 455/1000 * 1440 = 655 px
# At 96 DPI, 10.5pt = 10.5 * 96/72 = 14px per em
# Chinese char ≈ 14px wide; Latin char ≈ 7px wide

canvas_w = 1440
norm_box_w = 455
box_px = norm_box_w / 1000 * canvas_w
print(f"Textbox width in pixels: {box_px:.0f}px")

# The problematic line:
line = "• 建立新渠道试投池: 定向开发KOC种草、垂直社区等新型渠道，首批测试ROI达1:4.5"
chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff' or c in '：、，。。、！')
latin_chars = len(line) - chinese_chars
print(f"Line: {len(line)} chars ({chinese_chars} CJK, {latin_chars} latin)")

for pt in [10.5, 10, 9.5, 9]:
    px_per_em = pt * 96 / 72
    # CJK chars are full-width (1em), Latin chars are ~0.55em
    est_width = chinese_chars * px_per_em + latin_chars * px_per_em * 0.55
    fits = est_width <= box_px
    print(f"  {pt}pt: estimated width={est_width:.0f}px, fits in {box_px:.0f}px: {'✅' if fits else '❌ WRAPS'}")
