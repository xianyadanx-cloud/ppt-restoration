"""Coordinate conversions for the restoration Scene IR.

Pixels on the canonical image are authoritative.  Normalized coordinates are
only an import/compatibility format; they are never used for shape geometry in
the compiler.  The defaults are the project's 1440x810 reference canvas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple, Union

EMU_PER_INCH = 914400
PT_PER_INCH = 72.0
DEFAULT_DPI = 96.0
Number = Union[int, float]


@dataclass(frozen=True)
class CanvasSpec:
    width_px: int = 1440
    height_px: int = 810
    width_in: float = 13.333333333333334
    height_in: float = 7.5

    @property
    def width_emu(self) -> int:
        return int(round(self.width_in * EMU_PER_INCH))

    @property
    def height_emu(self) -> int:
        return int(round(self.height_in * EMU_PER_INCH))

    @property
    def aspect_ratio(self) -> float:
        return float(self.width_px) / float(self.height_px)


def _canvas(canvas: Union[CanvasSpec, Sequence[Number], None] = None) -> CanvasSpec:
    if canvas is None:
        return CanvasSpec()
    if isinstance(canvas, CanvasSpec):
        return canvas
    if len(canvas) == 2:
        return CanvasSpec(int(canvas[0]), int(canvas[1]))
    if len(canvas) == 4:
        return CanvasSpec(
            int(canvas[0]), int(canvas[1]), float(canvas[2]), float(canvas[3])
        )
    raise ValueError(
        "canvas must be CanvasSpec or (width_px, height_px[, width_in, height_in])"
    )


def px_to_emu(
    value_px: Number,
    axis: str = "x",
    canvas: Union[CanvasSpec, Sequence[Number], None] = None,
) -> int:
    """Convert canonical pixels to EMU using the physical slide dimension."""
    c = _canvas(canvas)
    if axis.lower() in ("y", "height", "v", "vertical"):
        return int(round(float(value_px) * c.height_emu / c.height_px))
    return int(round(float(value_px) * c.width_emu / c.width_px))


def emu_to_px(
    value_emu: Number,
    axis: str = "x",
    canvas: Union[CanvasSpec, Sequence[Number], None] = None,
) -> float:
    c = _canvas(canvas)
    if axis.lower() in ("y", "height", "v", "vertical"):
        return float(value_emu) * c.height_px / c.height_emu
    return float(value_emu) * c.width_px / c.width_emu


def px_to_pt(value_px: Number, dpi: float = DEFAULT_DPI) -> float:
    """Convert pixels to points for typography and margins (96 DPI by default)."""
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    return float(value_px) * PT_PER_INCH / float(dpi)


def pt_to_px(value_pt: Number, dpi: float = DEFAULT_DPI) -> float:
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    return float(value_pt) * float(dpi) / PT_PER_INCH


def pt_to_emu(value_pt: Number) -> int:
    return int(round(float(value_pt) * EMU_PER_INCH / PT_PER_INCH))


def emu_to_pt(value_emu: Number) -> float:
    return float(value_emu) * PT_PER_INCH / EMU_PER_INCH


def norm_to_px(
    value_norm: Number,
    axis: str = "x",
    canvas: Union[CanvasSpec, Sequence[Number], None] = None,
) -> float:
    c = _canvas(canvas)
    size = (
        c.height_px if axis.lower() in ("y", "height", "v", "vertical") else c.width_px
    )
    return float(value_norm) * size / 1000.0


def px_to_norm(
    value_px: Number,
    axis: str = "x",
    canvas: Union[CanvasSpec, Sequence[Number], None] = None,
) -> float:
    c = _canvas(canvas)
    size = (
        c.height_px if axis.lower() in ("y", "height", "v", "vertical") else c.width_px
    )
    return float(value_px) * 1000.0 / size


def box_px_to_emu(
    box: Sequence[Number], canvas: Union[CanvasSpec, Sequence[Number], None] = None
) -> Tuple[int, int, int, int]:
    if len(box) != 4:
        raise ValueError("box must be [left, top, width, height]")
    return (
        px_to_emu(box[0], "x", canvas),
        px_to_emu(box[1], "y", canvas),
        px_to_emu(box[2], "x", canvas),
        px_to_emu(box[3], "y", canvas),
    )


def norm_box_to_px(
    box: Sequence[Number], canvas: Union[CanvasSpec, Sequence[Number], None] = None
) -> Tuple[float, float, float, float]:
    if len(box) != 4:
        raise ValueError("box must be [left, top, width, height]")
    return (
        norm_to_px(box[0], "x", canvas),
        norm_to_px(box[1], "y", canvas),
        norm_to_px(box[2], "x", canvas),
        norm_to_px(box[3], "y", canvas),
    )


# Compatibility spellings used by early migration adapters.
pixels_to_emu = px_to_emu
emu_from_px = px_to_emu
px_box_to_emu = box_px_to_emu
norm_box_to_pixels = norm_box_to_px


def norm_to_emu(
    value_norm: Number,
    axis: str = "x",
    canvas: Union[CanvasSpec, Sequence[Number], None] = None,
) -> int:
    return px_to_emu(norm_to_px(value_norm, axis, canvas), axis, canvas)


__all__ = [
    "CanvasSpec",
    "EMU_PER_INCH",
    "px_to_emu",
    "pixels_to_emu",
    "emu_from_px",
    "emu_to_px",
    "px_to_pt",
    "pt_to_px",
    "pt_to_emu",
    "emu_to_pt",
    "norm_to_px",
    "norm_to_emu",
    "px_to_norm",
    "box_px_to_emu",
    "px_box_to_emu",
    "norm_box_to_px",
    "norm_box_to_pixels",
]
