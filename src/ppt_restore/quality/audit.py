"""Machine-verifiable boundary artifacts for the host multimodal agent.

The deterministic runtime does not call a vision model.  It prepares the
canonical image and evidence, accepts a SceneSpec proposal, and then checks a
second, explicit content-audit artifact against that proposal.  This module
keeps the two-pass hand-off inspectable without pretending that a local
algorithm can prove that the model read the source image correctly.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, fields
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from ppt_restore.contracts.schema_v2 import (
    EvidenceBundle,
    SceneNode,
    SceneSpecV2,
    scene_sha256,
)
from ppt_restore.quality.content_inventory import node_content

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_STATUSES = {"PROPOSED", "VALIDATED", "NEEDS_REVIEW"}
_ITEM_STATUSES = {"CONFIRMED", "VALIDATED", "NEEDS_REVIEW", "CONFLICT", "MISSING"}
_PASS_NAMES = {
    "pass_1_scene_extraction": ("pass_1_scene_extraction", "scene_extraction", "scene"),
    "pass_2_content_audit": ("pass_2_content_audit", "content_audit", "audit"),
}


def _clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_clean(item) for item in value]
    return value


def _strict(
    data: Mapping[str, Any], allowed: Iterable[str], required: Iterable[str] = ()
) -> None:
    if not isinstance(data, Mapping):
        raise TypeError("content audit must be a JSON object")
    unknown = set(data) - set(allowed)
    if unknown:
        raise ValueError(
            "unknown content audit field(s): %s"
            % ", ".join(sorted(str(item) for item in unknown))
        )
    missing = set(required) - set(data)
    if missing:
        raise ValueError(
            "missing content audit field(s): %s"
            % ", ".join(sorted(str(item) for item in missing))
        )


def _hash(value: Any, name: str) -> str:
    text = str(value or "")
    if not _SHA256.match(text):
        raise ValueError("%s must be a SHA-256 hex digest" % name)
    return text.lower()


def _confidence(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 1:
        raise ValueError("content audit confidence must be between 0 and 1")
    return result


def _box_norm(value: Any) -> Tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("content audit bbox_norm must contain four numbers")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError("content audit bbox_norm contains a non-finite value")
    if result[2] <= 0 or result[3] <= 0 or min(result) < 0:
        raise ValueError("content audit bbox_norm must be positive")
    if result[0] + result[2] > 1000 + 1e-6 or result[1] + result[3] > 1000 + 1e-6:
        raise ValueError("content audit bbox_norm must lie within 0-1000")
    return result  # type: ignore


@dataclass(frozen=True)
class ContentAudit:
    """Serialized pass-2 artifact submitted by the host multimodal agent.

    ``PROPOSED`` is the normal state at the agent boundary.  ``ingest``
    deterministically validates it and persists a validated SceneSpec only
    when the artifact has complete critical coverage and no conflicts.
    """

    schema_version: str
    canonical_sha256: str
    evidence_sha256: str
    scene_sha256: str
    status: str = "PROPOSED"
    passes: Mapping[str, Any] = None  # type: ignore
    items: Tuple[Mapping[str, Any], ...] = ()
    review_reasons: Tuple[str, ...] = ()
    source: str = "host_multimodal_agent"
    metadata: Mapping[str, Any] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("unsupported ContentAudit schema version")
        _hash(self.canonical_sha256, "canonical_sha256")
        _hash(self.evidence_sha256, "evidence_sha256")
        _hash(self.scene_sha256, "scene_sha256")
        if str(self.status) not in _STATUSES:
            raise ValueError("unsupported ContentAudit status: %s" % self.status)
        if not isinstance(self.passes or {}, Mapping):
            raise TypeError("content audit passes must be an object")
        if not isinstance(self.metadata or {}, Mapping):
            raise TypeError("content audit metadata must be an object")
        object.__setattr__(self, "passes", dict(self.passes or {}))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        object.__setattr__(
            self, "items", tuple(dict(item) for item in (self.items or ()))
        )
        object.__setattr__(
            self,
            "review_reasons",
            tuple(str(item) for item in (self.review_reasons or ())),
        )

    def to_dict(self) -> Dict[str, Any]:
        return _clean({field.name: getattr(self, field.name) for field in fields(self)})

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContentAudit":
        _strict(
            data,
            (
                "schema_version",
                "canonical_sha256",
                "evidence_sha256",
                "scene_sha256",
                "status",
                "passes",
                "items",
                "review_reasons",
                "source",
                "metadata",
            ),
            ("schema_version", "canonical_sha256", "evidence_sha256", "scene_sha256"),
        )
        kwargs = dict(data)
        kwargs["passes"] = dict(kwargs.get("passes", {}) or {})
        kwargs["items"] = tuple(dict(item) for item in (kwargs.get("items", ()) or ()))
        kwargs["review_reasons"] = tuple(
            str(item) for item in (kwargs.get("review_reasons", ()) or ())
        )
        kwargs["metadata"] = dict(kwargs.get("metadata", {}) or {})
        return cls(**kwargs)

    @classmethod
    def from_json(cls, value: str) -> "ContentAudit":
        return cls.from_dict(json.loads(value))


def content_audit_sha256(audit: ContentAudit) -> str:
    return hashlib.sha256(audit.to_json().encode("utf-8")).hexdigest()


def _stable_scene_sha256(scene: SceneSpecV2) -> str:
    """Hash the JSON-normalized proposal so int/float boxes round-trip alike."""

    normalized = SceneSpecV2.from_dict(json.loads(scene.to_json()))
    return scene_sha256(normalized)


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _norm_struct(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _norm_struct(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_norm_struct(item) for item in value]
    if isinstance(value, str):
        return _norm_text(value)
    return value


def _audit_item_content(item: Mapping[str, Any]) -> Dict[str, Any]:
    content = item.get("content")
    if isinstance(content, Mapping):
        return dict(content)
    keys = (
        "text",
        "values",
        "table_cells",
        "categories",
        "series",
        "label",
        "value",
        "delta",
        "steps",
    )
    return {key: item[key] for key in keys if key in item}


def _pass_value(
    passes: Mapping[str, Any], canonical_name: str
) -> Optional[Mapping[str, Any]]:
    for name in _PASS_NAMES[canonical_name]:
        value = passes.get(name)
        if isinstance(value, Mapping):
            return value
    return None


def _expected_bbox_norm(
    node: SceneNode, scene: SceneSpecV2
) -> Tuple[float, float, float, float]:
    width = float(scene.canvas.get("width_px", 0) or 0)
    height = float(scene.canvas.get("height_px", 0) or 0)
    x, y, w, h = node.bbox_px
    return (
        x * 1000.0 / width,
        y * 1000.0 / height,
        w * 1000.0 / width,
        h * 1000.0 / height,
    )


def validate_content_audit(
    audit: ContentAudit,
    scene: SceneSpecV2,
    evidence: Optional[EvidenceBundle] = None,
    *,
    canonical_sha256: Optional[str] = None,
    evidence_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate the host's two-pass artifact without invoking a model.

    A valid result proves only that the submitted audit covers the submitted
    SceneSpec and that deterministic references/content agree.  It does not
    prove that the model's interpretation of the original pixels is correct.
    """

    if not isinstance(audit, ContentAudit):
        audit = ContentAudit.from_dict(audit)  # type: ignore[arg-type]
    reasons: List[str] = list(audit.review_reasons)
    expected_canonical = str(canonical_sha256 or scene.canonical_sha256).lower()
    expected_evidence = str(evidence_sha256 or scene.evidence_sha256).lower()
    expected_scene = _stable_scene_sha256(scene)
    if audit.canonical_sha256.lower() != expected_canonical:
        reasons.append("content audit canonical_sha256 mismatch")
    if audit.evidence_sha256.lower() != expected_evidence:
        reasons.append("content audit evidence_sha256 mismatch")
    if audit.scene_sha256.lower() != expected_scene:
        reasons.append("content audit scene_sha256 mismatch")
    if audit.status == "NEEDS_REVIEW":
        reasons.append("content audit is already marked NEEDS_REVIEW")

    for pass_name in ("pass_1_scene_extraction", "pass_2_content_audit"):
        value = _pass_value(audit.passes, pass_name)
        if value is None:
            reasons.append("missing required pass artifact: %s" % pass_name)
            continue
        status = str(value.get("status", "")).strip().casefold()
        if status in ("", "awaiting", "missing", "blocked", "needs_review", "conflict"):
            reasons.append("%s is not complete" % pass_name)

    nodes = {node.id: node for node in scene.nodes}
    critical_nodes = {
        node.id: node
        for node in scene.nodes
        if node.role not in ("decoration", "container") and node.kind != "group"
    }
    seen: set = set()
    checked = []
    critical_confidences: List[float] = []
    for raw_item in audit.items:
        item = dict(raw_item)
        node_id = str(item.get("node_id", "")).strip()
        if not node_id:
            reasons.append("content audit item missing node_id")
            continue
        if node_id in seen:
            reasons.append("duplicate content audit item: %s" % node_id)
            continue
        seen.add(node_id)
        node = nodes.get(node_id)
        if node is None:
            reasons.append("content audit references unknown node: %s" % node_id)
            continue
        checked.append(node_id)
        status = str(item.get("status", "CONFIRMED")).upper()
        if status not in _ITEM_STATUSES:
            reasons.append("%s has unsupported audit status %s" % (node_id, status))
        elif status != "CONFIRMED" and status != "VALIDATED":
            reasons.append("%s content audit status is %s" % (node_id, status))
        try:
            confidence = _confidence(item.get("confidence", node.confidence))
            if node_id in critical_nodes:
                critical_confidences.append(confidence)
            if confidence < 0.80:
                reasons.append("%s audit confidence below 0.80" % node_id)
        except (TypeError, ValueError) as exc:
            reasons.append("%s invalid audit confidence: %s" % (node_id, exc))
        if "bbox_norm" not in item:
            reasons.append("%s missing bbox_norm" % node_id)
        else:
            try:
                supplied = _box_norm(item["bbox_norm"])
                expected = _expected_bbox_norm(node, scene)
                if any(abs(a - b) > 1.5 for a, b in zip(supplied, expected)):
                    reasons.append(
                        "%s audit bbox_norm disagrees with SceneSpec" % node_id
                    )
            except (TypeError, ValueError) as exc:
                reasons.append("%s invalid bbox_norm: %s" % (node_id, exc))
        if item.get("role") is not None and str(item["role"]) != str(node.role):
            reasons.append("%s audit role disagrees with SceneSpec" % node_id)
        if item.get("critical") is not None and bool(item["critical"]) != (
            node_id in critical_nodes
        ):
            reasons.append("%s audit critical flag disagrees with SceneSpec" % node_id)
        refs = tuple(str(ref) for ref in (item.get("evidence_refs", ()) or ()))
        if node.evidence_refs and not set(node.evidence_refs).issubset(set(refs)):
            reasons.append("%s audit evidence_refs omit SceneSpec references" % node_id)
        if evidence is not None:
            evidence_ids = set()
            for key in ("ocr_lines", "visual_primitives", "guides", "regions"):
                evidence_ids.update(
                    str(entry.get("id"))
                    for entry in getattr(evidence, key, ())
                    if entry.get("id")
                )
            missing_refs = [ref for ref in refs if ref not in evidence_ids]
            if missing_refs:
                reasons.append(
                    "%s audit references missing evidence: %s"
                    % (node_id, ", ".join(missing_refs))
                )

        expected_content = node_content(node)
        actual_content = _audit_item_content(item)
        if node_id in critical_nodes and expected_content and not actual_content:
            reasons.append("%s critical content audit item has no content" % node_id)
        for key, expected_value in expected_content.items():
            if key not in actual_content:
                reasons.append("%s audit omits content field %s" % (node_id, key))
                continue
            if _norm_struct(actual_content[key]) != _norm_struct(expected_value):
                reasons.append("%s audit content conflict in %s" % (node_id, key))

    missing = sorted(set(critical_nodes) - seen)
    reasons.extend(
        "missing critical content audit item: %s" % node_id for node_id in missing
    )
    calibration = (
        audit.metadata.get("confidence_calibration", {})
        if isinstance(audit.metadata, Mapping)
        else {}
    )
    independently_calibrated = bool(
        isinstance(calibration, Mapping)
        and calibration.get("independent_context") is True
        and str(calibration.get("method", "")).strip()
    )
    if (
        len(critical_confidences) >= 5
        and all(value >= 0.999 for value in critical_confidences)
        and not independently_calibrated
    ):
        reasons.append(
            "suspicious perfect audit confidence; supply independent confidence_calibration or mark uncertainty"
        )
    unique_reasons = list(dict.fromkeys(reasons))
    valid = not unique_reasons
    return {
        "schema_version": "1.0",
        "status": "VALIDATED" if valid else "NEEDS_REVIEW",
        "valid": valid,
        "review_reasons": unique_reasons,
        "checked_node_ids": sorted(checked),
        "critical_node_ids": sorted(critical_nodes),
        "missing_critical_node_ids": missing,
        "coverage": {
            "critical_total": len(critical_nodes),
            "critical_checked": len(set(critical_nodes) & seen),
            "item_total": len(audit.items),
        },
        "claim": "validates model-submitted audit against SceneSpec/evidence; does not prove source-image recognition correctness",
    }


def make_content_audit(
    scene: SceneSpecV2, *, status: str = "PROPOSED", confirmed: bool = False
) -> ContentAudit:
    """Create a deterministic fixture/template for a host agent to review.

    This helper is intentionally a template generator, not OCR or vision
    inference.  A host model should inspect the canonical image and edit the
    resulting item content before submitting the artifact.
    """

    items = []
    for node in scene.nodes:
        if node.role in ("decoration", "container") or node.kind == "group":
            continue
        items.append(
            {
                "node_id": node.id,
                "role": node.role,
                "kind": node.kind,
                "bbox_norm": list(_expected_bbox_norm(node, scene)),
                "status": "CONFIRMED" if confirmed else "NEEDS_REVIEW",
                "content": node_content(node),
                "confidence": float(node.confidence)
                if confirmed
                else min(0.5, float(node.confidence)),
                "evidence_refs": list(node.evidence_refs),
                "critical": True,
            }
        )
    return ContentAudit(
        schema_version="1.0",
        canonical_sha256=scene.canonical_sha256,
        evidence_sha256=scene.evidence_sha256,
        scene_sha256=_stable_scene_sha256(scene),
        status=status if confirmed else "NEEDS_REVIEW",
        passes={
            "pass_1_scene_extraction": {
                "status": "completed",
                "artifact": "scene.proposed.json",
            },
            "pass_2_content_audit": {
                "status": "completed" if confirmed else "awaiting",
                "artifact": "content_audit.proposed.json",
            },
        },
        items=tuple(items),
        review_reasons=()
        if confirmed
        else ("template only; host multimodal reviewer must inspect canonical image",),
    )


__all__ = [
    "ContentAudit",
    "content_audit_sha256",
    "validate_content_audit",
    "make_content_audit",
]
