"""Semantic SceneSpec v2 contracts.

SceneSpec v2 is the boundary between a multimodal host agent
and the deterministic PPT compiler: it describes semantic nodes, while the
compiler lowers those nodes into native drawing operations.

The module is deliberately dependency free and Python 3.9 compatible.  The
JSON contract is strict at the top level so malformed agent output cannot be
silently treated as a slide.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

BBox = Tuple[float, float, float, float]
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


class NodeKind(str, Enum):
    GROUP = "group"
    TEXT = "text"
    SHAPE = "shape"
    LINE = "line"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    KPI_CARD = "kpi_card"
    PROGRESS_BAR = "progress_bar"
    BADGE = "badge"
    PROCESS = "process"


class SemanticRole(str, Enum):
    TITLE = "title"
    BODY = "body"
    LABEL = "label"
    METRIC = "metric"
    TABLE = "table"
    CHART = "chart"
    CONTAINER = "container"
    DECORATION = "decoration"


class RenderStrategy(str, Enum):
    NATIVE = "native"
    RASTER = "raster"


def _clean(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            field.name: _clean(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_clean(item) for item in value]
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    return value


def _strict(
    data: Mapping[str, Any], allowed: Iterable[str], required: Iterable[str] = ()
) -> None:
    if not isinstance(data, Mapping):
        raise TypeError("expected JSON object")
    unknown = set(data) - set(allowed)
    if unknown:
        raise ValueError(
            "unknown field(s): %s" % ", ".join(sorted(str(item) for item in unknown))
        )
    missing = set(required) - set(data)
    if missing:
        raise ValueError(
            "missing field(s): %s" % ", ".join(sorted(str(item) for item in missing))
        )


def _bbox(value: Sequence[float], name: str = "bbox_px") -> BBox:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("%s must contain four numbers" % name)
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError("%s contains a non-finite value" % name)
    if result[2] <= 0 or result[3] <= 0:
        raise ValueError("%s width and height must be positive" % name)
    if result[0] < 0 or result[1] < 0:
        raise ValueError("%s left and top must be non-negative" % name)
    return result  # type: ignore


def _bbox_norm(value: Sequence[float], name: str = "bbox_norm") -> BBox:
    """Validate a public 0-1000 box before converting it to pixels."""

    result = _bbox(value, name)
    if (
        any(item > 1000 for item in result)
        or result[0] + result[2] > 1000 + 1e-6
        or result[1] + result[3] > 1000 + 1e-6
    ):
        raise ValueError("%s must lie within the 0-1000 coordinate system" % name)
    return result


def _confidence(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 1:
        raise ValueError("confidence must be between 0 and 1")
    return result


def _hash(value: Any, name: str) -> str:
    result = str(value or "")
    if result and not _SHA256.match(result):
        raise ValueError("%s must be a SHA-256 hex digest" % name)
    return result


@dataclass(frozen=True)
class EvidenceBundle:
    schema_version: str
    canonical_sha256: str
    canvas: Mapping[str, Any]
    ocr_lines: Tuple[Mapping[str, Any], ...] = ()
    visual_primitives: Tuple[Mapping[str, Any], ...] = ()
    palette: Tuple[Mapping[str, Any], ...] = ()
    guides: Tuple[Mapping[str, Any], ...] = ()
    regions: Tuple[Mapping[str, Any], ...] = ()
    artifacts: Tuple[Mapping[str, Any], ...] = ()
    producer: Mapping[str, Any] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("unsupported EvidenceBundle schema version")
        _hash(self.canonical_sha256, "canonical_sha256")
        if not isinstance(self.canvas, Mapping):
            raise TypeError("canvas must be an object")
        width = int(self.canvas.get("width_px", 0))
        height = int(self.canvas.get("height_px", 0))
        if width <= 0 or height <= 0:
            raise ValueError("canvas dimensions must be positive")
        if self.producer is None:
            object.__setattr__(self, "producer", {})

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceBundle":
        _strict(
            data,
            tuple(field.name for field in fields(cls)),
            ("schema_version", "canonical_sha256", "canvas"),
        )
        kwargs = dict(data)
        for key in (
            "ocr_lines",
            "visual_primitives",
            "palette",
            "guides",
            "regions",
            "artifacts",
        ):
            kwargs[key] = tuple(dict(item) for item in kwargs.get(key, ()) or ())
        kwargs["producer"] = dict(kwargs.get("producer", {}) or {})
        return cls(**kwargs)

    @classmethod
    def from_json(cls, value: str) -> "EvidenceBundle":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class SceneNode:
    id: str
    kind: str
    role: str
    bbox_px: BBox
    z_index: int = 0
    parent_id: Optional[str] = None
    confidence: float = 1.0
    render_strategy: str = RenderStrategy.NATIVE.value
    evidence_refs: Tuple[str, ...] = ()
    review_reasons: Tuple[str, ...] = ()
    payload: Mapping[str, Any] = None  # type: ignore
    style: Mapping[str, Any] = None  # type: ignore
    constraints: Tuple[Mapping[str, Any], ...] = ()
    block_id: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.kind, Enum):
            object.__setattr__(self, "kind", self.kind.value)
        if isinstance(self.role, Enum):
            object.__setattr__(self, "role", self.role.value)
        if isinstance(self.render_strategy, Enum):
            object.__setattr__(self, "render_strategy", self.render_strategy.value)
        if not str(self.id).strip():
            raise ValueError("node id must not be empty")
        try:
            NodeKind(str(self.kind))
        except ValueError:
            raise ValueError("unsupported node kind: %s" % self.kind)
        try:
            SemanticRole(str(self.role))
        except ValueError:
            raise ValueError("unsupported semantic role: %s" % self.role)
        try:
            RenderStrategy(str(self.render_strategy))
        except ValueError:
            raise ValueError("unsupported render strategy: %s" % self.render_strategy)
        _bbox(self.bbox_px)
        _confidence(self.confidence)
        if int(self.z_index) != self.z_index:
            raise ValueError("z_index must be an integer")
        if not isinstance(self.payload or {}, Mapping) or not isinstance(
            self.style or {}, Mapping
        ):
            raise TypeError("payload and style must be objects")
        if self.block_id is not None and not str(self.block_id).strip():
            raise ValueError("block_id must be non-empty when supplied")
        if self.payload is None:
            object.__setattr__(self, "payload", {})
        if self.style is None:
            object.__setattr__(self, "style", {})
        if str(self.kind) == NodeKind.TEXT.value and "text" not in (self.payload or {}):
            raise ValueError("text node payload must contain text")
        if str(self.kind) == NodeKind.IMAGE.value and not (
            {"source_bbox_px", "source_bbox_norm"} & set(self.payload or {})
        ):
            raise ValueError(
                "image node payload must contain source_bbox_norm or source_bbox_px"
            )
        if str(self.kind) == NodeKind.IMAGE.value and "source_bbox_norm" in (
            self.payload or {}
        ):
            _bbox_norm(self.payload["source_bbox_norm"], "source_bbox_norm")
        if str(self.kind) == NodeKind.TABLE.value and "cells" not in (
            self.payload or {}
        ):
            raise ValueError("table node payload must contain cells")
        if str(self.kind) == NodeKind.CHART.value:
            payload = self.payload or {}
            for key in ("chart_type", "categories", "series"):
                if key not in payload:
                    raise ValueError("chart node payload must contain %s" % key)

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any], *, canvas: Optional[Mapping[str, Any]] = None
    ) -> "SceneNode":
        # The external Agent contract is normalized 0-1000.  Internally we
        # persist pixel boxes because evidence and raster crops are pixel
        # addressed.  Conversion happens once, deterministically, at ingest.
        raw = dict(data)
        if "bbox_norm" in raw:
            if "bbox_px" in raw:
                raise ValueError("provide exactly one of bbox_norm or bbox_px")
            norm = _bbox_norm(raw.pop("bbox_norm"))
            if canvas is None:
                raise ValueError("canvas is required when bbox_norm is used")
            width = float(canvas.get("width_px", 0) or 0)
            height = float(canvas.get("height_px", 0) or 0)
            if width <= 0 or height <= 0:
                raise ValueError("canvas dimensions must be positive")
            raw["bbox_px"] = [
                norm[0] * width / 1000.0,
                norm[1] * height / 1000.0,
                norm[2] * width / 1000.0,
                norm[3] * height / 1000.0,
            ]
        _strict(
            raw,
            tuple(field.name for field in fields(cls)),
            ("id", "kind", "role", "bbox_px"),
        )
        kwargs = dict(raw)
        kwargs["bbox_px"] = _bbox(kwargs["bbox_px"])
        kwargs["evidence_refs"] = tuple(
            str(item) for item in kwargs.get("evidence_refs", ()) or ()
        )
        kwargs["review_reasons"] = tuple(
            str(item) for item in kwargs.get("review_reasons", ()) or ()
        )
        kwargs["constraints"] = tuple(
            dict(item) for item in kwargs.get("constraints", ()) or ()
        )
        kwargs["payload"] = dict(kwargs.get("payload", {}) or {})
        kwargs["style"] = dict(kwargs.get("style", {}) or {})
        return cls(**kwargs)


@dataclass(frozen=True)
class SceneSpecV2:
    schema_version: str
    canonical_sha256: str
    evidence_sha256: str
    canvas: Mapping[str, Any]
    nodes: Tuple[SceneNode, ...] = ()
    state: str = "PROPOSED"
    metadata: Mapping[str, Any] = None  # type: ignore
    blocks: Tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.state, Enum):
            object.__setattr__(self, "state", self.state.value)
        if self.schema_version != "2.0":
            raise ValueError("SceneSpecV2 schema_version must be '2.0'")
        _hash(self.canonical_sha256, "canonical_sha256")
        _hash(self.evidence_sha256, "evidence_sha256")
        if not isinstance(self.canvas, Mapping):
            raise TypeError("canvas must be an object")
        width = int(self.canvas.get("width_px", 0))
        height = int(self.canvas.get("height_px", 0))
        if width <= 0 or height <= 0:
            raise ValueError("canvas dimensions must be positive")
        allowed_states = {"PROPOSED", "VALIDATED", "NEEDS_REVIEW"}
        if str(self.state) not in allowed_states:
            raise ValueError("unsupported SceneSpec state: %s" % self.state)
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        normalized_blocks = tuple(dict(item) for item in (self.blocks or ()))
        object.__setattr__(self, "blocks", normalized_blocks)
        block_ids = [str(item.get("id", "")).strip() for item in normalized_blocks]
        if any(not item for item in block_ids):
            raise ValueError("SceneSpec block ids must not be empty")
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("SceneSpec block ids must be unique")
        for block in normalized_blocks:
            if "bbox_norm" not in block and "bbox_px" not in block:
                raise ValueError(
                    "SceneSpec block %s requires bbox_norm or bbox_px" % block.get("id")
                )
            if "bbox_norm" in block:
                _bbox_norm(block["bbox_norm"], "block bbox_norm")
            if "bbox_px" in block:
                _bbox(block["bbox_px"], "block bbox_px")
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("SceneSpec node ids must be unique")
        by_id = set(ids)
        for node in self.nodes:
            if node.parent_id and node.parent_id not in by_id:
                raise ValueError(
                    "node %s references missing parent %s" % (node.id, node.parent_id)
                )
            x, y, width_px, height_px = node.bbox_px
            if x + width_px > width + 1e-6 or y + height_px > height + 1e-6:
                raise ValueError("node %s lies outside the canvas" % node.id)
            if node.block_id and node.block_id not in set(block_ids):
                raise ValueError(
                    "node %s references missing block %s" % (node.id, node.block_id)
                )
            if (
                block_ids
                and node.role
                not in (SemanticRole.DECORATION.value, SemanticRole.CONTAINER.value)
                and not node.block_id
            ):
                raise ValueError(
                    "critical node %s requires block_id when SceneSpec blocks are declared"
                    % node.id
                )
        for node in self.nodes:
            seen = set()
            parent = node.parent_id
            while parent:
                if parent in seen:
                    raise ValueError("SceneSpec parent cycle detected")
                seen.add(parent)
                parent_node = next(item for item in self.nodes if item.id == parent)
                parent = parent_node.parent_id

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SceneSpecV2":
        _strict(
            data,
            tuple(field.name for field in fields(cls)),
            ("schema_version", "canonical_sha256", "evidence_sha256", "canvas"),
        )
        kwargs = dict(data)
        kwargs["nodes"] = tuple(
            SceneNode.from_dict(item, canvas=kwargs.get("canvas"))
            for item in kwargs.get("nodes", ()) or ()
        )
        kwargs["metadata"] = dict(kwargs.get("metadata", {}) or {})
        kwargs["blocks"] = tuple(dict(item) for item in kwargs.get("blocks", ()) or ())
        return cls(**kwargs)

    @classmethod
    def from_json(cls, value: str) -> "SceneSpecV2":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class RenderOp:
    id: str
    op_type: str
    bbox_px: BBox
    z_index: int = 0
    source_node_id: str = ""
    payload: Mapping[str, Any] = None  # type: ignore
    style: Mapping[str, Any] = None  # type: ignore

    def __post_init__(self) -> None:
        if not str(self.id).strip() or not str(self.op_type).strip():
            raise ValueError("RenderOp id and op_type are required")
        _bbox(self.bbox_px)
        if not isinstance(self.payload or {}, Mapping) or not isinstance(
            self.style or {}, Mapping
        ):
            raise TypeError("RenderOp payload and style must be objects")
        if self.payload is None:
            object.__setattr__(self, "payload", {})
        if self.style is None:
            object.__setattr__(self, "style", {})

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)


@dataclass(frozen=True)
class RenderPlan:
    schema_version: str
    scene_sha256: str
    canvas: Mapping[str, Any]
    operations: Tuple[RenderOp, ...] = ()
    warnings: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("unsupported RenderPlan schema version")
        _hash(self.scene_sha256, "scene_sha256")

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)


@dataclass(frozen=True)
class BuildManifest:
    """Hash binding for one deterministic SceneSpec build."""

    schema_version: str
    canonical_sha256: str
    evidence_sha256: str
    scene_sha256: str
    render_plan_sha256: str
    pptx_sha256: str
    compiler_version: str
    output_path: str
    created_utc: str = ""
    source: str = "scene_v2"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("unsupported BuildManifest schema version")
        for name in (
            "canonical_sha256",
            "evidence_sha256",
            "scene_sha256",
            "render_plan_sha256",
            "pptx_sha256",
        ):
            _hash(getattr(self, name), name)
        if not str(self.compiler_version).strip() or not str(self.output_path).strip():
            raise ValueError("compiler_version and output_path are required")

    def to_dict(self) -> Dict[str, Any]:
        return _clean(self)

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BuildManifest":
        _strict(
            data,
            tuple(field.name for field in fields(cls)),
            (
                "schema_version",
                "canonical_sha256",
                "evidence_sha256",
                "scene_sha256",
                "render_plan_sha256",
                "pptx_sha256",
                "compiler_version",
                "output_path",
            ),
        )
        return cls(**dict(data))

    @classmethod
    def from_json(cls, value: str) -> "BuildManifest":
        return cls.from_dict(json.loads(value))


def scene_sha256(scene: SceneSpecV2) -> str:
    """Hash canonical SceneSpec bytes used by build manifests."""

    import hashlib

    return hashlib.sha256(scene.to_json().encode("utf-8")).hexdigest()


def evidence_sha256(bundle: EvidenceBundle) -> str:
    import hashlib

    return hashlib.sha256(bundle.to_json().encode("utf-8")).hexdigest()


def render_plan_sha256(plan: RenderPlan) -> str:
    import hashlib

    return hashlib.sha256(plan.to_json().encode("utf-8")).hexdigest()


__all__ = [
    "BBox",
    "NodeKind",
    "SemanticRole",
    "RenderStrategy",
    "EvidenceBundle",
    "SceneNode",
    "SceneSpecV2",
    "RenderOp",
    "RenderPlan",
    "scene_sha256",
    "evidence_sha256",
    "render_plan_sha256",
    "BuildManifest",
]
