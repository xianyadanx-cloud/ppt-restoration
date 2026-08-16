"""PDF to Images Extractor.

Extracts slides from a multi-page PDF presentation into individual
high-resolution PNG images in input/ directory.
"""

import os
import sys
import shutil
import subprocess
import argparse
from PIL import Image


def extract_pdf_to_images(pdf_path: str, output_dir: str = "input", dpi: int = 150) -> list:
    """Extract all pages from a PDF file into PNG images."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    extracted_images = []

    # Try pdftoppm (poppler)
    if shutil.which("pdftoppm"):
        prefix = os.path.join(output_dir, f"{base_name}_slide")
        cmd = ["pdftoppm", "-png", "-r", str(dpi), pdf_path, prefix]
        subprocess.run(cmd, check=True)
        # Scan extracted files
        for fname in sorted(os.listdir(output_dir)):
            if fname.startswith(f"{base_name}_slide-") and fname.endswith(".png"):
                extracted_images.append(os.path.join(output_dir, fname))
    else:
        # Fallback to pypdf / pypdf + Pillow or pdf2image if available
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            print(f"[PDF Info] Found {total_pages} pages in {pdf_path}")
            
            # Check for embedded images per page
            for idx, page in enumerate(reader.pages, 1):
                count = 0
                for img_file_obj in page.images:
                    out_img_path = os.path.join(output_dir, f"{base_name}_slide_{idx:02d}.png")
                    with open(out_img_path, "wb") as fp:
                        fp.write(img_file_obj.data)
                    extracted_images.append(out_img_path)
                    count += 1
                    break
        except Exception as e:
            print(f"[Warning] Failed extraction via pypdf: {e}")

    if not extracted_images:
        print(f"[Notice] Tip: Install poppler for universal PDF page rendering: `brew install poppler`")
    else:
        print(f"[Success] Extracted {len(extracted_images)} slides to {output_dir}/")

    return extracted_images


def main():
    parser = argparse.ArgumentParser(description="Extract pages from a PDF presentation to slide images.")
    parser.add_argument("pdf_file", help="Input PDF file path")
    parser.add_argument("-o", "--output-dir", default="input", help="Output directory (default: input)")
    parser.add_argument("--dpi", type=int, default=150, help="Image resolution DPI (default: 150)")
    args = parser.parse_args()

    extract_pdf_to_images(args.pdf_file, args.output_dir, args.dpi)


if __name__ == "__main__":
    main()
