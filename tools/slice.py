"""High-precision Image Slicing Tool for PPT Restoration Workspace.

Crops sub-images, icons, photos, or micro-regions from slide images
using 0-1000 normalized coordinates [left, top, width, height].
"""

import os
import sys
import argparse
from typing import List, Tuple, Union
from PIL import Image


def slice_image(
    image_path: str,
    box: Union[List[float], Tuple[float, float, float, float]],
    output_path: str,
    padding_pct: float = 0.0,
) -> str:
    """Crop an image region using 0-1000 normalized coordinates.

    Args:
        image_path: Path to the source slide image.
        box: [left, top, width, height] normalized in 0-1000.
        output_path: Destination path for the cropped image.
        padding_pct: Optional safety padding around crop (in percentage 0-100).
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source image not found: {image_path}")

    with Image.open(image_path) as img:
        img_w, img_h = img.size
        l, t, w, h = box

        # Convert normalized 0-1000 to pixel bounding box
        px_left = (l / 1000.0) * img_w
        px_top = (t / 1000.0) * img_h
        px_width = (w / 1000.0) * img_w
        px_height = (h / 1000.0) * img_h

        # Apply padding if requested
        if padding_pct > 0:
            pad_w = px_width * (padding_pct / 100.0)
            pad_h = px_height * (padding_pct / 100.0)
            px_left = max(0, px_left - pad_w)
            px_top = max(0, px_top - pad_h)
            px_right = min(img_w, px_left + px_width + pad_w * 2)
            px_bottom = min(img_h, px_top + px_height + pad_h * 2)
        else:
            px_right = min(img_w, px_left + px_width)
            px_bottom = min(img_h, px_top + px_height)

        crop_box = (int(px_left), int(px_top), int(px_right), int(px_bottom))
        cropped = img.crop(crop_box)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cropped.save(output_path)
        print(f"[Success] Sliced region {box} -> {output_path} ({cropped.size[0]}x{cropped.size[1]} px)")
        return output_path


def main():
    parser = argparse.ArgumentParser(description="Crop sub-region from slide image using 0-1000 coordinates.")
    parser.add_argument("input", help="Source image path (e.g. input/slide_01.png)")
    parser.add_argument("--box", nargs=4, type=float, required=True, metavar=("LEFT", "TOP", "WIDTH", "HEIGHT"),
                        help="4 coordinates in 0-1000 scale: left top width height")
    parser.add_argument("-o", "--output", default="assets/crop.png", help="Output cropped image path")
    parser.add_argument("--padding", type=float, default=0.0, help="Optional padding percentage (e.g. 2)")

    args = parser.parse_args()
    slice_image(args.input, args.box, args.output, args.padding)


if __name__ == "__main__":
    main()
