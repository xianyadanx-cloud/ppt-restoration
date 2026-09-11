"""JSON-safe case and input registration models.

Models are deliberately dependency free.  ``from_dict`` rejects unknown keys
and invalid primitive values so malformed case files cannot silently enter a
build or verification run.
"""

import json
import math
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple

CURRENT_SCHEMA_VERSION = "1.0"
BBox = Tuple[float, float, float, float]
Point = Tuple[float, float]


class AnalysisState(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    ANALYZED = "ANALYZED"
    BUILT = "BUILT"
    PREVERIFIED = "PREVERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PASS = "PASS"
    FAIL = "FAIL"


# Names used by a few early callers; the serialized vocabulary remains the
# seven canonical values above.
PipelineState = AnalysisState
Status = AnalysisState


def _bbox(value: Sequence[float], name="bbox") -> BBox:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("%s must contain four numbers" % name)
    out = tuple(float(x) for x in value)
    if not all(math.isfinite(x) for x in out) or out[2] < 0 or out[3] < 0:
        raise ValueError("invalid %s" % name)
    return out  # type: ignore


def _point(value: Sequence[float]) -> Point:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("point must contain two numbers")
    out = (float(value[0]), float(value[1]))
    if not all(math.isfinite(x) for x in out):
        raise ValueError("invalid point")
    return out


def _confidence(value: float) -> float:
    value = float(value)
    if not 0 <= value <= 1 or not math.isfinite(value):
        raise ValueError("confidence must be between 0 and 1")
    return value


def _clean(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _clean(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple):
        return [_clean(x) for x in value]
    if isinstance(value, list):
        return [_clean(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    return value


def _strict(data: Mapping[str, Any], allowed, required=()):
    if not isinstance(data, Mapping):
        raise TypeError("expected JSON object")
    unknown = set(data) - set(allowed)
    if unknown:
        raise ValueError("unknown field(s): %s" % ", ".join(sorted(unknown)))
    missing = set(required) - set(data)
    if missing:
        raise ValueError("missing field(s): %s" % ", ".join(sorted(missing)))


@dataclass(frozen=True)
class Canvas:
    width_px: int
    height_px: int
    color_space: str = "sRGB"
    dpi: float = 96.0

    def __post_init__(self):
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("canvas dimensions must be positive")
        if self.color_space.lower() != "srgb":
            raise ValueError("only sRGB canvas output is supported")

    def to_dict(self):
        return _clean(self)

    @classmethod
    def from_dict(cls, d):
        _strict(
            d,
            ("width_px", "height_px", "color_space", "dpi"),
            ("width_px", "height_px"),
        )
        return cls(
            int(d["width_px"]),
            int(d["height_px"]),
            d.get("color_space", "sRGB"),
            float(d.get("dpi", 96)),
        )


@dataclass(frozen=True)
class Registration:
    input_sha256: str
    source_size_px: Tuple[int, int]
    target_size_px: Tuple[int, int]
    corners: Tuple[Point, Point, Point, Point]
    confidence: float
    method: str = "identity"
    edge_error_px: float = 0.0
    page_candidates: Tuple[BBox, ...] = ()
    color_space: str = "sRGB"
    canonical_sha256: str = ""
    state: AnalysisState = AnalysisState.ANALYZED

    @property
    def source_corners(self):
        return self.corners

    @property
    def page_size_px(self):
        return self.target_size_px

    def __post_init__(self):
        _confidence(self.confidence)
        if len(self.corners) != 4:
            raise ValueError("four registration corners required")
        for p in self.corners:
            _point(p)
        if self.edge_error_px < 0:
            raise ValueError("negative edge error")

    def to_dict(self):
        return _clean(self)

    @classmethod
    def from_dict(cls, d):
        names = tuple(f.name for f in fields(cls))
        _strict(
            d,
            names,
            (
                "input_sha256",
                "source_size_px",
                "target_size_px",
                "corners",
                "confidence",
            ),
        )
        kw = dict(d)
        kw["source_size_px"] = tuple(int(x) for x in kw["source_size_px"])
        kw["target_size_px"] = tuple(int(x) for x in kw["target_size_px"])
        kw["corners"] = tuple(_point(x) for x in kw["corners"])
        kw["page_candidates"] = tuple(_bbox(x) for x in kw.get("page_candidates", ()))
        kw["state"] = AnalysisState(kw.get("state", AnalysisState.ANALYZED))
        return cls(**kw)


@dataclass(frozen=True)
class CaseManifest:
    schema_version: str
    input_sha256: str
    target_canvas: Canvas
    primary_renderer: str = "powerpoint"
    compatibility_renderer: str = "libreoffice"
    fonts: Tuple[str, ...] = ()
    editability_strategy: str = "native_vector"
    state: AnalysisState = AnalysisState.INVALID_INPUT
    final_verdict: Optional[AnalysisState] = None
    tool_versions: Mapping[str, str] = field(default_factory=dict)
    operating_system: str = ""
    python_version: str = ""
    created_utc: str = ""

    @property
    def target_ratio(self) -> float:
        return self.target_canvas.width_px / float(self.target_canvas.height_px)

    @property
    def page_size_px(self) -> Tuple[int, int]:
        return (self.target_canvas.width_px, self.target_canvas.height_px)

    @property
    def current_stage(self) -> AnalysisState:
        return self.state

    def to_dict(self):
        return _clean(self)

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)

    @classmethod
    def from_dict(cls, d):
        _strict(
            d,
            tuple(f.name for f in fields(cls)),
            ("schema_version", "input_sha256", "target_canvas"),
        )
        kw = dict(d)
        kw["target_canvas"] = Canvas.from_dict(kw["target_canvas"])
        kw["state"] = AnalysisState(kw.get("state", AnalysisState.INVALID_INPUT))
        kw["final_verdict"] = (
            AnalysisState(kw["final_verdict"]) if kw.get("final_verdict") else None
        )
        kw["fonts"] = tuple(kw.get("fonts", ()))
        return cls(**kw)

    @classmethod
    def from_json(cls, value):
        return cls.from_dict(json.loads(value))
