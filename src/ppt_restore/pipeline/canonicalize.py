"""Deterministic input normalization and page registration.

This module deliberately uses Pillow only.  OpenCV/numpy can be added as an
accelerator later, but the baseline must produce the same bytes on every
supported Python platform.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageCms

from ppt_restore.contracts.models import (
    AnalysisState,
    Canvas,
    CaseManifest,
    Registration,
)
from ppt_restore.platform.io import (
    create_case_dir,
    sha256_file,
    write_case_manifest,
    write_registration,
)

Point = Tuple[float, float]
Corners = Tuple[Point, Point, Point, Point]
DEFAULT_CANVAS = (1440, 810)


def _srgb(image: Image.Image) -> Image.Image:
    """Convert embedded ICC profiles to sRGB when Pillow can do so."""
    image.load()
    profile = image.info.get("icc_profile")
    rgb = image.convert("RGB")
    if profile:
        try:
            src = ImageCms.ImageCmsProfile(__import__("io").BytesIO(profile))
            dst = ImageCms.createProfile("sRGB")
            rgb = ImageCms.profileToProfile(rgb, src, dst, outputMode="RGB")
        except Exception:
            # Keeping RGB pixels is safer than inventing a color transform.
            pass
    return rgb


def _identity_corners(size: Tuple[int, int]) -> Corners:
    w, h = size
    return ((0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h)))


def _is_target_ratio(size, target) -> bool:
    return abs((size[0] / float(size[1])) / (target[0] / float(target[1])) - 1) <= 0.001


def _row_darkness(image: Image.Image, rows: int = 160) -> List[float]:
    small = image.convert("L").resize((80, rows), Image.Resampling.BILINEAR)
    values = []
    for y in range(rows):
        values.append(sum(small.getpixel((x, y)) for x in range(80)) / 80.0)
    return values


def detect_page_candidates(
    image: Image.Image, target_ratio: float = 16 / 9
) -> List[Tuple[int, int, int, int]]:
    """Find plausible pages in a long image using deterministic row runs."""
    w, h = image.size
    if _is_target_ratio((w, h), (16, 9)):
        return [(0, 0, w, h)]
    rgb = image.convert("RGB")
    # Long screenshots commonly place page rectangles on a uniform gray
    # pasteboard.  Estimate that pasteboard from the perimeter, then locate
    # large non-background row runs.  This avoids assuming pages start at y=0
    # or occupy the full screenshot width.
    perimeter = []
    stride = max(1, min(w, h) // 360)
    for x in range(0, w, stride):
        perimeter.extend((rgb.getpixel((x, 0)), rgb.getpixel((x, h - 1))))
    for y in range(0, h, stride):
        perimeter.extend((rgb.getpixel((0, y)), rgb.getpixel((w - 1, y))))
    background = Counter(perimeter).most_common(1)[0][0]
    differs = lambda pixel: (
        max(abs(int(pixel[i]) - int(background[i])) for i in range(3)) > 12
    )
    x_step = max(1, w // 480)
    sampled_x = list(range(0, w, x_step))
    active_rows = []
    for y in range(h):
        active = sum(1 for x in sampled_x if differs(rgb.getpixel((x, y))))
        active_rows.append(active >= len(sampled_x) * 0.55)
    runs = []
    start = None
    for y, active in enumerate(active_rows + [False]):
        if active and start is None:
            start = y
        elif not active and start is not None:
            if y - start >= 60:
                runs.append((start, y))
            start = None
    candidates = []
    for top, bottom in runs:
        y_step = max(1, (bottom - top) // 240)
        sampled_y = list(range(top, bottom, y_step))
        active_columns = []
        for x in range(w):
            count = sum(1 for y in sampled_y if differs(rgb.getpixel((x, y))))
            if count >= len(sampled_y) * 0.55:
                active_columns.append(x)
        if not active_columns:
            continue
        left, right = min(active_columns), max(active_columns) + 1
        page = (left, top, right - left, bottom - top)
        if (
            page[2] >= w * 0.50
            and abs((page[2] / float(page[3])) / target_ratio - 1) <= 0.08
        ):
            candidates.append(page)
    # If no boundary is visible, deterministic ratio windows are still useful.
    # Compare against the expected *page height*, not width.  A two-page
    # landscape strip is commonly only 1.1x as tall as it is wide.
    if not candidates and h > (w / target_ratio) * 1.25:
        ph = int(round(w / target_ratio))
        for top in range(0, h - ph + 1, ph):
            candidates.append((0, top, w, ph))
    return candidates


def detect_canvas_bounds(
    image: Image.Image, target_ratio: float = 16 / 9
) -> Tuple[Tuple[int, int, int, int], float]:
    """Detect a light canvas boundary; return bbox and confidence."""
    w, h = image.size
    if _is_target_ratio((w, h), (16, 9)):
        return (0, 0, w, h), 1.0
    rgb = image.convert("RGB")
    # Compare edge pixels to corner/background color.  This catches white
    # screenshot margins without classifying interior text as a border.
    corner = rgb.getpixel((0, 0))

    def close(p):
        return sum(abs(int(p[i]) - int(corner[i])) for i in range(3)) <= 18

    xs = [
        x
        for x in range(w)
        if not close(rgb.getpixel((x, 0))) or not close(rgb.getpixel((x, h - 1)))
    ]
    ys = [
        y
        for y in range(h)
        if not close(rgb.getpixel((0, y))) or not close(rgb.getpixel((w - 1, y)))
    ]
    if xs and ys:
        left, right = min(xs), max(xs) + 1
        top, bottom = min(ys), max(ys) + 1
        candidate = (left, top, right - left, bottom - top)
        if (
            candidate[2] >= 64
            and candidate[3] >= 64
            and abs((candidate[2] / candidate[3]) / target_ratio - 1) < 0.06
        ):
            return candidate, 0.94
    # Center crop gives a stable fallback, but is explicitly low confidence.
    if w / float(h) > target_ratio:
        cw, ch = int(round(h * target_ratio)), h
    else:
        cw, ch = w, int(round(w / target_ratio))
    return ((w - cw) // 2, (h - ch) // 2, cw, ch), 0.72


def _quad_transform(
    image: Image.Image, corners: Corners, size: Tuple[int, int]
) -> Image.Image:
    # Pillow QUAD expects upper-left, lower-left, lower-right, upper-right.
    ul, ur, lr, ll = corners
    data = (ul[0], ul[1], ll[0], ll[1], lr[0], lr[1], ur[0], ur[1])
    return image.transform(
        size, Image.Transform.QUAD, data, resample=Image.Resampling.BICUBIC
    )


def canonicalize(
    input_path: Union[str, Path],
    case_dir: Union[str, Path],
    *,
    target_size=DEFAULT_CANVAS,
    corners: Optional[Sequence[Sequence[float]]] = None,
    page_index: int = 0,
    primary_renderer: str = "powerpoint",
) -> Registration:
    """Normalize an image into ``case_dir/canonical.png`` and write artifacts."""
    source = Path(input_path)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(str(source))
    root = create_case_dir(case_dir)
    input_hash = sha256_file(source)
    if page_index < 0:
        raise IndexError("page_index must be non-negative")
    # Pillow may appear to open PDFs on some machines through an optional
    # delegate, but that is not reproducible.  Always rasterize explicitly
    # with pdftoppm and fail with an actionable message when unavailable.
    raster_tmp = None
    image_source = source
    if source.suffix.casefold() == ".pdf":
        executable = shutil.which("pdftoppm")
        if not executable:
            raise RuntimeError(
                "PDF input requires pdftoppm; install Poppler or provide a raster image"
            )
        raster_tmp = tempfile.TemporaryDirectory(prefix="pptrestore-pdf-")
        prefix = Path(raster_tmp.name) / "page"
        command = [
            executable,
            "-f",
            str(page_index + 1),
            "-l",
            str(page_index + 1),
            "-png",
            "-singlefile",
            str(source),
            str(prefix),
        ]
        try:
            subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=120,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raster_tmp.cleanup()
            raise RuntimeError(
                "unable to rasterize PDF page %d with pdftoppm: %s"
                % (page_index + 1, exc)
            ) from exc
        image_source = prefix.with_suffix(".png")
        if not image_source.exists():
            raster_tmp.cleanup()
            raise RuntimeError(
                "pdftoppm produced no raster for PDF page %d" % (page_index + 1)
            )
    try:
        with Image.open(image_source) as opened:
            image = _srgb(opened)
    finally:
        # Keep the PIL image detached from the temporary PDF raster before
        # deleting the directory; ``_srgb`` has already loaded all pixels.
        if raster_tmp is not None:
            raster_tmp.cleanup()
    src_size = image.size
    candidates = detect_page_candidates(image)
    confidence = 1.0
    method = "pdf_page" if source.suffix.casefold() == ".pdf" else "identity"
    if corners is not None:
        if len(corners) != 4:
            raise ValueError("corners must contain four points")
        c = tuple((float(p[0]), float(p[1])) for p in corners)  # type: ignore
        normalized = _quad_transform(image, c, target_size)  # type: ignore
        confidence, method = 0.99, "explicit_quad"
    else:
        if candidates and len(candidates) > 1:
            if page_index < 0 or page_index >= len(candidates):
                raise IndexError("page_index out of range")
            box = candidates[page_index]
            image = image.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
            src_size = image.size
            method = "long_image_page"
        box, confidence = detect_canvas_bounds(image)
        image = image.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
        normalized = image.resize(target_size, Image.Resampling.LANCZOS)
        if method == "identity" and box != (0, 0, src_size[0], src_size[1]):
            method = "detected_canvas"
    normalized = normalized.convert("RGB")
    canonical = root / "canonical.png"
    normalized.save(canonical, format="PNG", optimize=False)
    canonical_hash = sha256_file(canonical)
    corners_out = (
        _identity_corners(src_size)
        if corners is None
        else tuple((float(p[0]), float(p[1])) for p in corners)
    )
    state = AnalysisState.ANALYZED if confidence >= 0.90 else AnalysisState.NEEDS_REVIEW
    registration = Registration(
        input_hash,
        src_size,
        tuple(target_size),
        corners_out,
        confidence,
        method,
        0.0,
        tuple(tuple(float(x) for x in c) for c in candidates),
        "sRGB",
        canonical_hash,
        state,
    )
    write_registration(root, registration)
    # Copying source bytes keeps provenance local and avoids changing input.
    source_copy = root / "source" / source.name
    if not source_copy.exists():
        source_copy.write_bytes(source.read_bytes())
    manifest = CaseManifest(
        schema_version="1.0",
        input_sha256=input_hash,
        target_canvas=Canvas(*target_size),
        primary_renderer=primary_renderer,
        state=state,
        final_verdict=None,
        operating_system=platform.platform(),
        python_version=platform.python_version(),
        tool_versions={"ppt_restore": "0.1.0", "Pillow": Image.__version__},
    )
    write_case_manifest(root, manifest)
    return registration


def canonicalize_image(input_path, case_dir, **kwargs):
    """Compatibility alias used by early pipeline prototypes."""
    return canonicalize(input_path, case_dir, **kwargs)
