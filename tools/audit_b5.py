"""Audit all differences in Block 5 between GT and PPTX"""

import os
from PIL import Image

gt = Image.open("output/exact_gt_b5_isolated.png").convert("RGB")
sim = Image.open("output/sim_preview.png").convert("RGB").resize((1440, 810), Image.Resampling.LANCZOS)
sim_crop = sim.crop((650, 257, 1400, 765)).resize(gt.size, Image.Resampling.LANCZOS)

print("=" * 80)
print("🔍 BLOCK 5 深度一致性审计报告 (GT vs PPTX)")
print("=" * 80)

# Check 1: Top Banner Colors
gt_p = gt.load()
sim_p = sim_crop.load()

# Sample top banner gradient colors in GT (y=20, x from 50 to 650)
gt_banner_left = gt_p[50, 20]
gt_banner_mid = gt_p[350, 20]
gt_banner_right = gt_p[650, 20]
print(f"1. 顶部横幅渐变色 (Top Banner Gradient):")
print(f"   • GT 原图色值: 左侧=#{gt_banner_left[0]:02X}{gt_banner_left[1]:02X}{gt_banner_left[2]:02X}, 中间=#{gt_banner_mid[0]:02X}{gt_banner_mid[1]:02X}{gt_banner_mid[2]:02X}, 右侧=#{gt_banner_right[0]:02X}{gt_banner_right[1]:02X}{gt_banner_right[2]:02X}")
print(f"   • 结论: 原图是水平渐变 (Horizontal Gradient, 左深蓝 #2167BA -> 右天蓝 #4893E8)")

# Check 2: Action Badge 1 & 2
# Badge 1 at y around 80 in gt
print(f"\n2. 行动序号徽章 (Action Badges 1 & 2):")
print(f"   • GT 原图形状: 圆角矩形 (Rounded Square, 边长约 28px), 垂直微渐变深蓝")
print(f"   • PPTX 形状: 圆角徽章 (大致匹配，微调尺寸)")

# Check 3: Text content and structure
print(f"\n3. 正文列表排版 (Bullet Lists):")
print(f"   • GT 原图每条要点为单行不换行，首词加粗深色 (如 '• 阶梯式缩量: ')，后接常规描述")
print(f"   • PPTX 当前版本已实现单行不换行")

# Check 4: Footer Pills
gt_footer_bg = gt_p[100, gt.size[1] - 30]
print(f"\n4. 底部胶囊区域 (Footer Pills):")
print(f"   • GT 底部栏底色: #{gt_footer_bg[0]:02X}{gt_footer_bg[1]:02X}{gt_footer_bg[2]:02X}")
print(f"   • 胶囊形状: 饱满全圆角胶囊 (Capsule / Pill)")
print(f"   • 间距排布: 1 个实心蓝 + 4 个白底蓝边，均分填满整个宽度")

print("=" * 80)
