"""Visual Verification & Side-by-Side Comparison Tool.

Renders generated PPTX to images (via OfficeCLI, Keynote AppleScript,
or LibreOffice) and stitches a side-by-side comparison with the original slide image.
"""

import os
import sys
import shutil
import subprocess
import argparse
from PIL import Image, ImageDraw, ImageFont

# Ensure repo root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def render_pptx_to_image(pptx_path: str, output_img_path: str, slide_index: int = 1) -> bool:
    """Render a slide from PPTX to an image using multi-level fallback strategies."""
    os.makedirs(os.path.dirname(os.path.abspath(output_img_path)), exist_ok=True)

    # Strategy 1: Check for OfficeCLI
    if shutil.which("officecli"):
        print("[Verify] Using OfficeCLI to render slide...")
        cmd = ["officecli", "render", pptx_path, f"/slide[{slide_index}]", "-o", output_img_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(output_img_path):
            return True

    # Strategy 2: macOS Keynote AppleScript (if on macOS)
    if sys.platform == "darwin":
        applescript = f'''
        tell application "Keynote"
            set doc to open POSIX file "{os.path.abspath(pptx_path)}"
            export doc to POSIX file "{os.path.abspath(output_img_path)}" as slide images with properties {{image format:PNG}}
            close doc saving no
        end tell
        '''
        try:
            res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                # Keynote exports as directory or image prefix
                if os.path.exists(output_img_path):
                    return True
                # Check for folder output slide.001.png
                base_dir = os.path.splitext(output_img_path)[0]
                possible_file = f"{base_dir}.001.png"
                if os.path.exists(possible_file):
                    shutil.move(possible_file, output_img_path)
                    return True
        except Exception:
            pass

    # Strategy 3: LibreOffice / soffice CLI
    soffice_bin = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice_bin:
        print("[Verify] Using LibreOffice to convert PPTX to PDF/Image...")
        temp_dir = os.path.join(os.path.dirname(output_img_path), "_temp_render")
        os.makedirs(temp_dir, exist_ok=True)
        cmd = [soffice_bin, "--headless", "--convert-to", "pdf", pptx_path, "--outdir", temp_dir]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        pdf_file = os.path.join(temp_dir, os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf")
        if os.path.exists(pdf_file):
            # Render PDF to image using pypdf/Pillow or pdftoppm
            pdftoppm = shutil.which("pdftoppm")
            if pdftoppm:
                subprocess.run([pdftoppm, "-png", "-r", "150", "-f", str(slide_index), "-l", str(slide_index), pdf_file, os.path.join(temp_dir, "slide")])
                rendered_page = os.path.join(temp_dir, f"slide-{slide_index:02d}.png")
                if not os.path.exists(rendered_page):
                    rendered_page = os.path.join(temp_dir, "slide-1.png")
                if os.path.exists(rendered_page):
                    shutil.move(rendered_page, output_img_path)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return True
            shutil.rmtree(temp_dir, ignore_errors=True)

    return False


def create_side_by_side_diff(
    original_img_path: str,
    rendered_img_path: str,
    diff_output_path: str,
) -> str:
    """Stitch original and rendered images side-by-side with header labels."""
    if not os.path.exists(original_img_path):
        raise FileNotFoundError(f"Original image not found: {original_img_path}")
    if not os.path.exists(rendered_img_path):
        raise FileNotFoundError(f"Rendered image not found: {rendered_img_path}")

    img_orig = Image.open(original_img_path).convert("RGB")
    img_rend = Image.open(rendered_img_path).convert("RGB")

    # Match heights
    target_height = 900
    w_orig = int(img_orig.width * (target_height / float(img_orig.height)))
    w_rend = int(img_rend.width * (target_height / float(img_rend.height)))

    img_orig_resized = img_orig.resize((w_orig, target_height), Image.Resampling.LANCZOS)
    img_rend_resized = img_rend.resize((w_rend, target_height), Image.Resampling.LANCZOS)

    header_h = 60
    border_w = 4
    total_w = w_orig + w_rend + border_w * 3
    total_h = target_height + header_h + border_w * 2

    canvas = Image.new("RGB", (total_w, total_h), color=(241, 245, 249))
    draw = ImageDraw.Draw(canvas)

    # Draw header bar
    draw.rectangle([0, 0, total_w, header_h], fill=(15, 23, 42))
    # Draw title text
    draw.text((border_w + 20, 18), "ORIGINAL SLIDE (INPUT)", fill=(148, 163, 184))
    draw.text((w_orig + border_w * 2 + 20, 18), "RESTORED PPTX RENDERING (OUTPUT)", fill=(56, 189, 248))

    # Paste images
    canvas.paste(img_orig_resized, (border_w, header_h + border_w))
    canvas.paste(img_rend_resized, (w_orig + border_w * 2, header_h + border_w))

    os.makedirs(os.path.dirname(os.path.abspath(diff_output_path)), exist_ok=True)
    canvas.save(diff_output_path)
    print(f"[Success] Visual comparison generated: {diff_output_path}")
    return diff_output_path


def main():
    parser = argparse.ArgumentParser(description="Verify PPTX output against original image.")
    parser.add_argument("original_image", help="Original slide image (e.g. input/slide_01.png)")
    parser.add_argument("pptx_file", help="Generated .pptx file (e.g. output/slide_01.pptx)")
    parser.add_argument("-o", "--output", default=None, help="Diff comparison image path")
    parser.add_argument("--slide", type=int, default=1, help="Slide index (default: 1)")

    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.original_image))[0]
    preview_img = f"output/preview_{base_name}.png"
    diff_img = args.output or f"output/diff_{base_name}.png"

    print(f"\n🔍 Verifying: {args.pptx_file} vs {args.original_image}")
    success = render_pptx_to_image(args.pptx_file, preview_img, args.slide)

    if success:
        create_side_by_side_diff(args.original_image, preview_img, diff_img)
        print(f"\n✨ Visual diff saved to: {diff_img}")
    else:
        print("\n[Notice] No local PPTX rendering binary (OfficeCLI / Keynote / LibreOffice) was detected.")
        print("Running PPTX structural inspection instead:")
        from tools.inspect_pptx import inspect_pptx
        inspect_pptx(args.pptx_file)
        print("\n💡 Tip: To enable automatic screenshot visual diffs, install OfficeCLI:")
        print("   macOS: brew install officecli   OR   npm install -g @officecli/officecli\n")


if __name__ == "__main__":
    main()
