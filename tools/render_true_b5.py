"""Accurate Block 5 Crop without KPI leakage"""

import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.render_and_diff import compare_and_generate_diff

# Let's test crop_box with top=360 so it cuts strictly below the KPI cards
compare_and_generate_diff(
    "input/slide_02.png",
    "output/sim_preview.png",
    "output/diff_block5_true_crop.png",
    crop_box=[460, 360, 520, 580],
    block_title="Block 5: True Strategy Card"
)
print("Saved output/diff_block5_true_crop.png")
