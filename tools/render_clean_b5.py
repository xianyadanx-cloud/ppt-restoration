"""Render Clean Block 5 Diff without Block 3 Leakage"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import compare_and_generate_diff

# 0-1000 Crop Box:
# Left: 475, Top: 308, Width: 495, Height: 620
# (Y=308 is exactly the top edge of Block 5 blue banner, completely below Block 3)
compare_and_generate_diff(
    "input/slide_02.png",
    "output/sim_preview.png",
    "output/diff_block5_clean.png",
    crop_box=[475, 308, 495, 620],
    block_title="Block 5: Accurate Clean Crop"
)
print("Saved clean Block 5 diff to output/diff_block5_clean.png")
