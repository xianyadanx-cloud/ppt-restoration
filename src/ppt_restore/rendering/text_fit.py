"""Closed-form font size and text-frame fit from an ink bounding box.

The host often measures the dark pixels of a line.  A text frame's top sits
above that ink by the font's ascent gap, and the point size follows the
canonical canvas (1440 px = 13.333 in = 960 pt), not a 96 DPI screenshot.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence, Tuple

from ppt_restore.rendering.geometry import CanvasSpec, px_to_pt

try:
    from fontTools.ttLib import TTFont
except ImportError:  # pragma: no cover - fonttools is optional at runtime
    TTFont = None


# Fallback when the face cannot be opened.  Values are em fractions close to
# Noto Sans CJK / Source Han Sans: ascent above the em square, ideograph body
# near 0.88 em, and a small left side bearing.
# Noto Sans CJK SC, measured from the Regular face (U+4E2D).  Used when the
# face cannot be opened.  ascent/descent are hhea/em; ymax/ymin are the
# ideograph ink box.
_FALLBACK_METRICS = {
    "ascent": 1.16,
    "descent": 0.288,
    "ymax": 0.84,
    "ymin": -0.08,
    "lsb": 0.08,
    "advance": 1.0,
}


def canvas_dpi(canvas: Optional[CanvasSpec] = None) -> float:
    """Pixels per inch of the physical slide, not the 96 DPI CSS default."""

    spec = canvas or CanvasSpec()
    if spec.width_in <= 0:
        raise ValueError("canvas width_in must be positive")
    return float(spec.width_px) / float(spec.width_in)


def px_to_pt_canvas(value_px: float, canvas: Optional[CanvasSpec] = None) -> float:
    return px_to_pt(value_px, canvas_dpi(canvas))


_REGISTRY = None


def _registry():
    global _REGISTRY
    if _REGISTRY is None:
        from ppt_restore.rendering.fonts import FontRegistry

        _REGISTRY = FontRegistry()
    return _REGISTRY


def _font_path(family: Optional[str], weight: Optional[int], sample: str):
    if not family:
        return None
    try:
        info = _registry().find(family, text=sample or "A", weight=weight)
    except (LookupError, OSError, ValueError):
        return None
    if info is None:
        return None
    return info.path, info.font_number


def _glyph_bounds(font, glyph_name):
    if "glyf" in font and glyph_name in font["glyf"]:
        glyph = font["glyf"][glyph_name]
        y_min = getattr(glyph, "yMin", None)
        y_max = getattr(glyph, "yMax", None)
        if y_min is None or y_max is None:
            return None
        return (
            getattr(glyph, "xMin", 0),
            y_min,
            getattr(glyph, "xMax", 0),
            y_max,
        )
    if "CFF " in font:
        try:
            charstring = font["CFF "].cff.topDictIndex[0].CharStrings[glyph_name]
            return charstring.calcBounds(None)
        except (AttributeError, KeyError, ValueError, TypeError):
            return None
    return None


def _em_metrics(family: Optional[str], weight: Optional[int], sample: str) -> dict:
    located = _font_path(family, weight, sample)
    if TTFont is None or located is None:
        return dict(_FALLBACK_METRICS)
    path, number = located
    try:
        font = TTFont(path, lazy=True, fontNumber=number)
    except (OSError, ValueError):
        return dict(_FALLBACK_METRICS)
    try:
        upem = float(font["head"].unitsPerEm) or 1000.0
        hhea = font["hhea"]
        ascent = float(hhea.ascent) / upem
        descent = abs(float(hhea.descent)) / upem
        cmap = font.getBestCmap() or {}
        hmtx = font["hmtx"].metrics
        ymax = ymin = None
        advance = 0.0
        counted = 0
        lsb = 0.0
        for index, char in enumerate(sample or "字"):
            glyph_name = cmap.get(ord(char))
            if glyph_name is None or glyph_name not in hmtx:
                continue
            adv, left = hmtx[glyph_name]
            advance += float(adv) / upem
            counted += 1
            if index == 0:
                lsb = float(left) / upem
            bounds = _glyph_bounds(font, glyph_name)
            if bounds is None:
                continue
            _x_min, y_min, _x_max, y_max = bounds
            if y_max is None or y_min is None:
                continue
            ymax = float(y_max) / upem if ymax is None else max(ymax, float(y_max) / upem)
            ymin = float(y_min) / upem if ymin is None else min(ymin, float(y_min) / upem)
        if counted == 0 or ymax is None or ymin is None:
            return dict(_FALLBACK_METRICS)
        return {
            "ascent": max(ascent, ymax),
            "descent": max(descent, abs(min(0.0, ymin))),
            "ymax": ymax,
            "ymin": ymin,
            "lsb": max(0.0, lsb),
            "advance": advance / counted,
        }
    finally:
        font.close()


def _line_advance(line: str, family: Optional[str], weight: Optional[int]) -> float:
    metrics = _em_metrics(family, weight, line or "字")
    # Per-character average advance times length.  CJK faces are nearly
    # monospaced; Latin strings still get a usable width from the same face.
    if not line:
        return metrics["advance"]
    located = _font_path(family, weight, line)
    if TTFont is None or located is None:
        return metrics["advance"] * max(1, len(line))
    path, number = located
    try:
        font = TTFont(path, lazy=True, fontNumber=number)
    except (OSError, ValueError):
        return metrics["advance"] * max(1, len(line))
    try:
        upem = float(font["head"].unitsPerEm) or 1000.0
        cmap = font.getBestCmap() or {}
        hmtx = font["hmtx"].metrics
        total = 0.0
        for char in line:
            glyph_name = cmap.get(ord(char))
            if glyph_name is None or glyph_name not in hmtx:
                total += metrics["advance"] * upem
            else:
                total += float(hmtx[glyph_name][0])
        return total / upem
    finally:
        font.close()


def expand_ink_frame(
    ink_bbox: Sequence[float],
    font_size_pt: float,
    canvas: Optional[CanvasSpec] = None,
    ascent_gap_em: Optional[float] = None,
    descent_pad_em: Optional[float] = None,
    side_bearing_em: float = 0.04,
) -> Tuple[float, float, float, float]:
    """Lift an ink box into a text frame that clears the font ascent."""

    spec = canvas or CanvasSpec()
    size_px = float(font_size_pt) / px_to_pt_canvas(1.0, spec)
    gap = 0.22 if ascent_gap_em is None else float(ascent_gap_em)
    descent = 0.16 if descent_pad_em is None else float(descent_pad_em)
    side = max(0.0, float(side_bearing_em)) * size_px
    shift = gap * size_px
    x, y, width, height = [float(value) for value in ink_bbox]
    return (
        x - side,
        y - shift,
        width + side * 2.0,
        height + shift + descent * size_px,
    )


def fit_text_frame(
    text: str,
    ink_bbox: Sequence[float],
    *,
    family: Optional[str] = None,
    weight: Optional[int] = None,
    canvas: Optional[CanvasSpec] = None,
    width_slack: float = 1.06,
) -> Mapping[str, object]:
    """Return ``font_size_pt`` and a frame bbox from a measured ink box.

    ``ink_bbox`` is ``(left, top, width, height)`` in canonical pixels.  The
    frame is expanded upward by the ascent gap so glyphs land on the ink
    instead of sitting below it.  No renderer is invoked.
    """

    spec = canvas or CanvasSpec()
    lines = str(text).split("\n") if text else [""]
    lines = lines or [""]
    x, y, width, height = [float(value) for value in ink_bbox]
    sample = max(lines, key=len) or "字"
    metrics = _em_metrics(family, weight, sample)
    # ymin may be negative.  The ink height is ymax - ymin.
    body = max(0.15, float(metrics["ymax"]) - float(metrics["ymin"]))
    count = max(1, len(lines))
    if height <= 0:
        size_px = 12.0
    elif count == 1:
        size_px = height / body
    else:
        # Ink stacks line bodies with a modest gap.  The last line has no
        # trailing gap, so the divisor is ``count * body + (count-1) * gap``.
        gap = body * 0.28
        size_px = height / (count * body + (count - 1) * gap)
    advance = _line_advance(sample, family, weight)
    # Height of the ink is the stable size signal.  Width only pulls the size
    # down when the fallback advance would overflow the measured ink.
    if advance > 0 and width > 0 and size_px * advance > width * 1.4:
        size_px = width / advance
    size_px = max(1.0, size_px)
    font_size_pt = px_to_pt_canvas(size_px, spec)
    ascent_gap = max(0.0, float(metrics["ascent"]) - float(metrics["ymax"]))
    side = max(0.0, float(metrics["lsb"])) * size_px
    frame_width = max(width, advance * size_px) * float(width_slack) + side
    line_pitch = (float(metrics["ascent"]) + float(metrics["descent"])) * size_px
    frame_height = line_pitch * count + 0.12 * size_px * max(0, count - 1)
    frame = (
        x - side,
        y - ascent_gap * size_px,
        frame_width,
        max(height, frame_height),
    )
    return {
        "font_size_pt": font_size_pt,
        "bbox_px": frame,
        "size_px": size_px,
        "ascent_gap_em": ascent_gap,
        "metrics_em": metrics,
    }
