"""Fine-tune exact coordinates for Slide 02."""

from PIL import Image

img = Image.open("output/inspect/canvas_slide_02.png")
cw, ch = img.size
print(f"Slide Canvas Dimensions: {cw} x {ch}")

# Let's measure positions relative to the canvas (0-1000 scale)
# Let's define the exact 0-1000 blueprint:

# Top Header:
# Title "季度工作攻坚策略": [35, 45, 550, 48]
# Divider Line: [35, 102, 930, 2]
# Right Author: [790, 52, 175, 36]

# Top Summary Banner:
# Container: [35, 120, 930, 80]
# Left Badge: [35, 120, 85, 80]
# Right Text: [135, 130, 815, 60]

# Middle Subtitle & KPI Cards:
# Subtitle Title: [35, 222, 430, 32]
# Subtitle Desc: [35, 258, 430, 55]

# KPI Cards:
# Card 1: [485, 215, 130, 105]
# Top Tag: [515, 203, 70, 24]
# Value: [485, 235, 130, 40]
# Bottom Pill: [505, 285, 90, 25]

# Arrow 1: [628, 255, 24, 24]

# Card 2: [660, 215, 130, 105]
# Top Tag: [690, 203, 70, 24]
# Value: [660, 235, 130, 40]
# Bottom Pill: [680, 285, 90, 25]

# Arrow 2: [803, 255, 24, 24]

# Card 3: [835, 215, 130, 105]
# Top Tag: [865, 203, 70, 24]
# Value: [835, 235, 130, 40]
# Bottom Pill: [855, 285, 90, 25]

# Bottom Section: y = 345 to 945 (height 600)
# Left Clipboard:
# Base Plate: [35, 345, 435, 595]
# Top Metallic Clip: [220, 335, 65, 16]
# Inner Paper: [43, 355, 419, 575]
# Paper Title: [45, 372, 415, 30]
# Table: [55, 415, 395, 490]
# Table Header: height 45, Rows: 5 rows of height 85 each!
# Progress Bars in Column 4:
# Row 1: y = 502
# Row 2: y = 590
# Row 3: y = 678
# Row 4: y = 766
# Row 5: y = 854

# Right Strategy Card:
# Container: [485, 345, 480, 595]
# Header Blue Block: [485, 345, 480, 75]
# "2+1": [498, 350, 70, 58]
# "破局行动": [575, 362, 105, 42]
# Quote Pill: [685, 365, 270, 34]
# Action Card 1: [498, 435, 454, 205]
# Action Card 2: [498, 655, 454, 205]
# Footer Bar: [485, 875, 480, 55]
# Footer Badges: y = 887, height 32
