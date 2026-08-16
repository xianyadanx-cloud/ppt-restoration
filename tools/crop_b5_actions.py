"""Crop the action sections from Block 5 diff for pixel-level analysis."""
from PIL import Image

img = Image.open("output/diff_block5_true_verified.png")
w, h = img.size
print(f"图片尺寸: {w}x{h}")

half = w // 2

# 截取整个行动1+2区域 (header大约从y=100开始, 底部药丸在y=390左右)
# 原图左半: 行动区域
left_actions = img.crop((0, 90, half, 380))
left_actions.save("output/debug_b5_actions_orig.png")

# PPTX右半: 行动区域
right_actions = img.crop((half, 90, w, 380))
right_actions.save("output/debug_b5_actions_pptx.png")

# 更精细: 只截取行动1 标题行 (序号+大标题)
left_title1 = img.crop((0, 90, half, 160))
left_title1.save("output/debug_b5_title1_orig.png")
right_title1 = img.crop((half, 90, w, 160))
right_title1.save("output/debug_b5_title1_pptx.png")

# 行动2 标题行
left_title2 = img.crop((0, 220, half, 300))
left_title2.save("output/debug_b5_title2_orig.png")
right_title2 = img.crop((half, 220, w, 300))
right_title2.save("output/debug_b5_title2_pptx.png")

print("截图完成。")
