"""Multi-Slide Deck Merger.

Combines individual output/slide_*.pptx files into a single unified
presentation presentation_final.pptx.
"""

import os
import sys
import glob
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pptx import Presentation


def merge_pptx_files(pptx_files: list, output_path: str = "output/final_deck.pptx") -> str:
    if not pptx_files:
        raise ValueError("No PPTX files provided to merge.")

    print(f"📦 Merging {len(pptx_files)} PPTX files into {output_path}...")
    master_prs = Presentation(pptx_files[0])
    slide_w = master_prs.slide_width
    slide_h = master_prs.slide_height

    for file_path in pptx_files[1:]:
        print(f"  + Appending {file_path}")
        sub_prs = Presentation(file_path)
        for slide in sub_prs.slides:
            # Add slide using blank layout from master
            blank_layout = master_prs.slide_layouts[6]
            new_slide = master_prs.slides.add_slide(blank_layout)

            # Copy background fill if available
            try:
                if slide.background.fill.type is not None:
                    new_slide.background.fill.solid()
                    new_slide.background.fill.fore_color.rgb = slide.background.fill.fore_color.rgb
            except Exception:
                pass

            # Copy all shapes from source slide to new slide
            for shape in slide.shapes:
                try:
                    # Note: python-pptx XML element deep copy
                    new_slide.shapes._spTree.append(shape._element)
                except Exception as e:
                    print(f"    [Warning] Failed copying shape: {e}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    master_prs.save(output_path)
    print(f"\n🎉 Successfully merged all slides into: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Merge multiple single-slide PPTX files into one presentation.")
    parser.add_argument("files", nargs="*", help="List of PPTX files to merge (optional, defaults to output/slide_*.pptx)")
    parser.add_argument("-o", "--output", default="output/final_deck.pptx", help="Final output PPTX path")
    parser.add_argument("--dir", default="output", help="Directory to search for slide_*.pptx")

    args = parser.parse_args()

    if args.files:
        files_to_merge = args.files
    else:
        files_to_merge = sorted(glob.glob(os.path.join(args.dir, "slide_*.pptx")))
        if not files_to_merge:
            files_to_merge = sorted(glob.glob(os.path.join(args.dir, "*.pptx")))
            # Exclude existing final output
            files_to_merge = [f for f in files_to_merge if os.path.basename(f) != os.path.basename(args.output)]

    if not files_to_merge:
        print(f"[Error] No PPTX files found to merge in {args.dir}/")
        sys.exit(1)

    merge_pptx_files(files_to_merge, args.output)


if __name__ == "__main__":
    main()
