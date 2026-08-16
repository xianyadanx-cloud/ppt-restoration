"""Test color_profiler on true banner location Y=470 (px=381)."""
import sys, os
sys.path.insert(0, os.path.abspath("."))
from tools.color_profiler import profile_block

# Normalized box for banner in original image:
# Left=480, Top=470 (381px), Width=494, Height=95 (77px)
res = profile_block("input/slide_02.png", [480, 470, 494, 95])
import json
print(json.dumps(res, indent=2, ensure_ascii=False))
