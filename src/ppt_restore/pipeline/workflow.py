"""Prepare/ingest orchestration for the host multimodal Agent."""

from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from ppt_restore.contracts.schema_v2 import EvidenceBundle, SceneNode, SceneSpecV2
from ppt_restore.platform.evidence import extract_evidence, read_evidence
from ppt_restore.platform.io import write_json
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.audit import ContentAudit, validate_content_audit
from ppt_restore.quality.content_inventory import (
    scene_to_content_inventory,
    write_content_inventory,
)

PathLike = Union[str, Path]


def _bbox_overlap(a, b) -> float:
    ax, ay, aw, ah = [float(x) for x in a]
    bx, by, bw, bh = [float(x) for x in b]
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    return intersection / max(1e-9, min(aw * ah, bw * bh))


def _text_values(node: SceneNode) -> List[str]:
    payload = node.payload or {}
    values = []
    if isinstance(payload.get("text"), str):
        values.append(payload["text"])
    runs = payload.get("runs")
    if isinstance(runs, list):
        values.append(
            "".join(
                str(run.get("text", "")) for run in runs if isinstance(run, Mapping)
            )
        )
    cells = payload.get("cells")
    if isinstance(cells, list):
        for row in cells:
            if isinstance(row, list):
                for cell in row:
                    if isinstance(cell, Mapping) and isinstance(cell.get("text"), str):
                        values.append(cell["text"])
                    elif isinstance(cell, str):
                        values.append(cell)
    return [value.strip() for value in values if value.strip()]


def _evidence_ids(bundle: EvidenceBundle) -> set:
    result = set()
    for key in ("ocr_lines", "visual_primitives", "guides", "regions"):
        result.update(
            str(item.get("id")) for item in getattr(bundle, key) if item.get("id")
        )
    return result


def validate_scene_proposal(
    scene: SceneSpecV2, evidence: EvidenceBundle
) -> Tuple[SceneSpecV2, Dict[str, Any]]:
    """Validate semantic references and return a review-aware SceneSpec."""

    evidence_ids = _evidence_ids(evidence)
    ocr = list(evidence.ocr_lines)
    review: List[str] = []
    updated: List[SceneNode] = []
    critical_nodes = [
        node for node in scene.nodes if node.role not in ("decoration", "container")
    ]
    for node in scene.nodes:
        # review_reasons are runtime-owned output.  Do not carry stale
        # reasons from a previous failed proposal into a repaired ingest.
        reasons: List[str] = []
        if node.role not in ("decoration", "container") and not node.evidence_refs:
            reasons.append("critical semantic node has no evidence_refs")
        missing = [ref for ref in node.evidence_refs if ref not in evidence_ids]
        if missing:
            reasons.append("missing evidence reference(s): %s" % ", ".join(missing))
        values = _text_values(node)
        for row in ocr:
            row_text = str(row.get("text", "")).strip()
            if not row_text or float(row.get("confidence", 0.0)) < 0.90:
                continue
            if _bbox_overlap(node.bbox_px, row.get("bbox_px", (0, 0, 0, 0))) < 0.10:
                continue
            if values and not any(
                row_text in value or value in row_text for value in values
            ):
                reasons.append("OCR conflict near %s: %s" % (node.id, row_text))
            if node.render_strategy == "raster" and node.role != "decoration":
                reasons.append("critical OCR overlaps raster node")
        if float(node.confidence) < 0.80:
            reasons.append("confidence below 0.80")
        if (
            node.kind == "image"
            and node.role != "decoration"
            and node.render_strategy == "raster"
        ):
            reasons.append("non-decoration image requires review")
        if (
            node.kind == "image"
            and node.render_strategy == "raster"
            and node.role == "decoration"
        ):
            if any(
                _bbox_overlap(node.bbox_px, other.bbox_px) >= 0.25
                for other in critical_nodes
                if other.id != node.id
            ):
                reasons.append("raster decoration overlaps critical semantic content")
        if reasons:
            review.extend("%s: %s" % (node.id, reason) for reason in reasons)
        updated.append(replace(node, review_reasons=tuple(dict.fromkeys(reasons))))
    # High-confidence OCR is a completeness signal, not merely a conflict
    # detector.  A proposal that silently drops a visible title/number must
    # stop for review even when all of its own nodes look internally valid.
    for row in ocr:
        row_text = str(row.get("text", "")).strip()
        if not row_text or float(row.get("confidence", 0.0)) < 0.95:
            continue
        covered = False
        for node in scene.nodes:
            if node.role in ("decoration", "container") or node.kind not in (
                "text",
                "table",
                "chart",
                "kpi_card",
                "badge",
                "process",
            ):
                continue
            if _bbox_overlap(node.bbox_px, row.get("bbox_px", (0, 0, 0, 0))) < 0.10:
                continue
            values = _text_values(node)
            if any(row_text in value or value in row_text for value in values):
                covered = True
                break
        if not covered:
            review.append(
                "%s: OCR line not covered by a semantic text/data node"
                % row.get("id", "ocr")
            )
    critical_confidences = [float(node.confidence) for node in critical_nodes]
    calibration = (scene.metadata or {}).get("confidence_calibration", {})
    calibrated = bool(
        isinstance(calibration, Mapping)
        and str(calibration.get("method", "")).strip()
        and calibration.get("independent_context") is True
    )
    if (
        len(critical_confidences) >= 5
        and all(value >= 0.999 for value in critical_confidences)
        and not calibrated
    ):
        review.append(
            "SceneSpec has suspicious perfect confidence on every critical node; calibrate independently or record uncertainty"
        )
    state = "NEEDS_REVIEW" if review else "VALIDATED"
    return replace(scene, nodes=tuple(updated), state=state), {
        "valid": not bool(review),
        "review_reasons": review,
    }


def prepare_case(
    input_path: PathLike,
    case_dir: PathLike,
    *,
    page_index: int = 0,
    ocr_mode: str = "auto",
    primary_renderer: str = "powerpoint",
) -> Dict[str, Any]:
    """Canonicalize an input and produce the Agent's request bundle."""

    from ppt_restore.pipeline.canonicalize import canonicalize

    root = Path(case_dir)
    registration = canonicalize(
        input_path, root, page_index=page_index, primary_renderer=primary_renderer
    )
    evidence_path = root / "evidence.json"
    bundle = extract_evidence(
        root / "canonical.png", ocr_mode=ocr_mode, output_path=evidence_path
    )
    producer = dict(bundle.producer or {})
    ocr_status = str(producer.get("ocr_status", "unavailable"))
    ocr_lines = len(bundle.ocr_lines)
    ocr_degraded = bool(producer.get("ocr_degraded", ocr_status != "completed"))
    ocr_zero = bool(producer.get("ocr_zero_detections", ocr_lines == 0))
    if ocr_status == "disabled":
        degradation_reason = (
            "OCR was disabled by request; inspect canonical.png for all critical text"
        )
    elif ocr_status == "zero_detections":
        degradation_reason = "OCR providers completed but returned zero detections"
    elif ocr_status in ("failed", "unavailable"):
        degradation_reason = "All configured OCR providers failed or were unavailable"
    else:
        degradation_reason = None
    request = {
        "protocol_version": "1.0",
        "scene_schema_version": "2.0",
        "case_dir": str(root.resolve()),
        "canonical_path": str((root / "canonical.png").resolve()),
        "canonical_sha256": sha256_file(root / "canonical.png"),
        "evidence_path": str(evidence_path.resolve()),
        "evidence_sha256": sha256_file(evidence_path),
        "scene_output_path": str((root / "scene.proposed.json").resolve()),
        "content_audit_output_path": str(
            (root / "content_audit.proposed.json").resolve()
        ),
        "prompt_template": str((root / "scene_spec_v2.md").resolve()),
        "canvas": bundle.canvas,
        "multimodal_protocol": {
            "name": "canonical_primary_two_pass",
            "primary_evidence": "canonical.png",
            "primary_evidence_path": str((root / "canonical.png").resolve()),
            "ocr_role": "cross_check_only",
            "model_execution": "host_agent_required; deterministic runtime never invokes a model",
            "passes": {
                "pass_1_scene_extraction": {
                    "artifact": str((root / "scene.proposed.json").resolve()),
                    "status": "AWAITING",
                    "purpose": "propose semantic SceneSpec v2 geometry, roles, styles, and evidence_refs",
                },
                "pass_2_content_audit": {
                    "artifact": str((root / "content_audit.proposed.json").resolve()),
                    "status": "AWAITING",
                    "purpose": "re-read canonical image and audit title, body, numbers, percentages, units, table cells, labels, and footnotes",
                },
            },
            "build_requires_both_passes": True,
        },
        "coordinate_contract": {
            "public_space": "0-1000 normalized",
            "field": "bbox_norm",
            "conversion": "ingest deterministically converts bbox_norm to persisted bbox_px using canvas width_px/height_px",
            "boxes": "[left, top, width, height]; left/top and right/bottom must remain within 0..1000",
            "image_source_boxes": "source_bbox_norm uses the same 0-1000 space",
            "freeform_geometry": "points_norm uses the same 0-1000 space",
        },
        "allowed_node_kinds": [
            "group",
            "text",
            "shape",
            "line",
            "image",
            "table",
            "chart",
            "kpi_card",
            "progress_bar",
            "badge",
            "process",
        ],
        "allowed_roles": [
            "title",
            "body",
            "label",
            "metric",
            "table",
            "chart",
            "container",
            "decoration",
        ],
        "render_strategy_rules": {
            "critical_roles_must_be_native": [
                "title",
                "body",
                "label",
                "metric",
                "table",
                "chart",
            ],
            "raster_allowed_roles": ["decoration"],
            "raster_allowed_for": "complex artwork or decoration only; never visible critical text, numbers, tables, chart labels, or business shapes",
            "minimum_confidence_without_review": 0.80,
        },
        "ocr": {
            "requested_mode": ocr_mode,
            "status": ocr_status,
            "selected_provider": producer.get("ocr_provider"),
            "attempts": list(producer.get("ocr_attempts", [])),
            "line_count": ocr_lines,
            "zero_detections": ocr_zero,
            "degraded": ocr_degraded,
            "warnings": list(producer.get("warning", [])),
        },
        "degradation": {
            "active": ocr_degraded,
            "reason": degradation_reason,
            "canonical_image_is_authoritative": True,
            "critical_text_review_required": bool(ocr_degraded or ocr_zero),
            "do_not_infer_text_absence_from_empty_ocr": True,
        },
        "validation_requirements": {
            "ingest_required_before_build": True,
            "repair_all_review_reasons": True,
            "exact_hashes_required": True,
            "all_nodes_require_evidence_refs": True,
            "critical_text_and_data_native": True,
            "high_confidence_ocr_lines_must_be_covered": True,
            "boxes_must_stay_within_canvas": True,
            "content_audit_required_for_new_multimodal_runs": True,
            "content_inventory_required_before_build": True,
            "dom_content_reconciliation_required_after_build": True,
            "return_only_scene_spec_json": True,
            "perfect_confidence_requires_independent_calibration": True,
            "critical_nodes_require_block_id_when_blocks_are_declared": True,
            "reference_specific_visuals_must_be_atomic_nodes": True,
        },
        "instructions": "Pass 1: inspect canonical.png directly and return one valid SceneSpecV2 JSON object using bbox_norm [left, top, width, height] in the public 0-1000 coordinate system (do not emit bbox_px). Declare macro blocks and assign block_id to every critical node. Decompose reference-specific visuals into atomic native nodes: floating tabs, layered boards, shadows, gradients, arrows, progress tracks/fills/markers, row strips, and text runs must not be collapsed into generic cards. Image crops use source_bbox_norm and freeform vertices use points_norm in the same system. Pass 2: re-open canonical.png in an independent review context and submit content_audit.proposed.json, checking every title, body line, number, percentage, unit, table cell, label, footnote, bbox, and visual hierarchy against the SceneSpec. Record calibrated confidence and uncertainty; do not mark every node 1.0 without an independent confidence_calibration record. OCR is cross-check only: if it is degraded or zero-detection, inspect canonical.png directly and never infer that empty OCR means the slide has no text. The deterministic runtime does not call a model and cannot prove source-image recognition correctness.",
        "evidence_warnings": list(producer.get("warning", [])),
        "review_artifacts": {
            "scene_extraction": str((root / "scene.proposed.json").resolve()),
            "content_audit": str((root / "content_audit.proposed.json").resolve()),
            "content_inventory": str((root / "content_inventory.json").resolve()),
            "dom_reconciliation_report": str(
                (root / "reports" / "content_dom_check.json").resolve()
            ),
        },
    }
    (root / "scene_spec_v2.md").write_text(
        files("ppt_restore")
        .joinpath("resources", "scene_spec_v2.md")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    write_json(root / "agent_request.json", request)
    return {
        "case_dir": str(root),
        "registration": registration.to_dict(),
        "evidence": str(evidence_path),
        "agent_request": str(root / "agent_request.json"),
        "status": "AWAITING_MULTIMODAL_SCENE_AND_AUDIT",
        "scene_proposed": str(root / "scene.proposed.json"),
        "content_audit_proposed": str(root / "content_audit.proposed.json"),
        "ocr_lines": ocr_lines,
        "ocr": request["ocr"],
        "degradation": request["degradation"],
        "evidence_warnings": list(producer.get("warning", [])),
    }


def ingest_scene(
    case_dir: PathLike,
    proposed_path: PathLike,
    content_audit_path: Optional[PathLike] = None,
    *,
    audit_path: Optional[PathLike] = None,
    allow_missing_audit: bool = False,
) -> Dict[str, Any]:
    """Validate a host Agent proposal and persist it only when structurally valid.

    New v2 cases require the host's pass-2 audit.  ``allow_missing_audit`` is
    an explicit switch for unaudited v2 experiments; it persists a compatibility
    warning and marks the resulting scene accordingly rather than silently
    presenting it as a fully audited multimodal run.
    """

    root = Path(case_dir)
    if content_audit_path is None:
        content_audit_path = audit_path
    canonical = root / "canonical.png"
    evidence_path = root / "evidence.json"
    if not canonical.is_file() or not evidence_path.is_file():
        return {
            "status": "INVALID_INPUT",
            "errors": ["canonical.png and evidence.json are required"],
        }
    try:
        evidence = read_evidence(evidence_path)
        scene = SceneSpecV2.from_json(Path(proposed_path).read_text(encoding="utf-8"))
        from ppt_restore.pipeline.revisions import assert_ingest_scope

        assert_ingest_scope(root, scene)
    except (OSError, TypeError, ValueError) as exc:
        result = {"status": "INVALID_INPUT", "errors": [str(exc)]}
        write_json(root / "reports" / "ingest.json", result)
        return result
    audit = None
    audit_report = {
        "status": "NOT_PROVIDED_COMPATIBILITY",
        "valid": True,
        "review_reasons": [],
    }
    audit_file_hash = None
    if content_audit_path is not None:
        try:
            audit_file = Path(content_audit_path)
            audit = ContentAudit.from_json(audit_file.read_text(encoding="utf-8"))
            audit_file_hash = sha256_file(audit_file)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            result = {
                "status": "INVALID_INPUT",
                "errors": ["invalid content audit: %s" % exc],
            }
            write_json(root / "reports" / "content_audit.json", result)
            write_json(root / "reports" / "ingest.json", result)
            return result
    errors = []
    if scene.canonical_sha256 != sha256_file(canonical):
        errors.append("canonical_sha256 mismatch")
    if scene.evidence_sha256 != sha256_file(evidence_path):
        errors.append("evidence_sha256 mismatch")
    if evidence.canonical_sha256 != sha256_file(canonical):
        errors.append("evidence canonical_sha256 mismatch")
    if errors:
        result = {"status": "INVALID_INPUT", "errors": errors}
        write_json(root / "reports" / "ingest.json", result)
        return result
    if content_audit_path is None and not allow_missing_audit:
        audit_report = {
            "schema_version": "1.0",
            "status": "NEEDS_REVIEW",
            "valid": False,
            "review_reasons": ["pass_2_content_audit is required for v2 ingest"],
            "warning": "No content_audit.proposed.json was supplied; submit the host pass-2 audit before build",
            "required_artifact": str((root / "content_audit.proposed.json").resolve()),
        }
        write_json(root / "reports" / "content_audit.json", audit_report)
        result = {
            "status": "NEEDS_REVIEW",
            "audit": audit_report,
            "report": audit_report,
            "warnings": [audit_report["warning"]],
        }
        write_json(root / "reports" / "ingest.json", result)
        return result
    validated, report = validate_scene_proposal(scene, evidence)
    if content_audit_path is None and allow_missing_audit:
        audit_report = {
            "schema_version": "1.0",
            "status": "MISSING_COMPATIBILITY",
            "valid": True,
            "review_reasons": [],
            "warning": "Content audit omitted under explicit compatibility mode; source text completeness is not audited",
            "required_artifact": str((root / "content_audit.proposed.json").resolve()),
        }
        write_json(root / "reports" / "content_audit.json", audit_report)
    if audit is not None:
        audit_report = validate_content_audit(
            audit,
            scene,
            evidence,
            canonical_sha256=sha256_file(canonical),
            evidence_sha256=sha256_file(evidence_path),
        )
        write_json(root / "reports" / "content_audit.json", audit_report)
        if not audit_report.get("valid", False):
            report = dict(report)
            report["review_reasons"] = list(
                dict.fromkeys(
                    list(report.get("review_reasons", []))
                    + list(audit_report.get("review_reasons", []))
                )
            )
            report["valid"] = False
    if not report["valid"]:
        # Persist the proposal for inspection, but never overwrite the formal
        # build input until a human/Agent resolves the review reasons.
        write_json(root / "scene.proposed.validated.json", validated)
        result = {
            "status": "NEEDS_REVIEW",
            "scene": str(root / "scene.proposed.validated.json"),
            "report": report,
            "audit": audit_report,
        }
        write_json(root / "reports" / "ingest.json", result)
        return result
    metadata = dict(validated.metadata or {})
    metadata.setdefault("render_strategy", "hybrid_editable")
    metadata.setdefault("persisted_coordinate_space", "px")
    metadata["multimodal_protocol"] = "canonical_primary_two_pass"
    metadata["content_audit_status"] = audit_report.get(
        "status", "NOT_PROVIDED_COMPATIBILITY"
    )
    if audit_file_hash:
        metadata["content_audit_file_sha256"] = audit_file_hash
    validated = replace(validated, metadata=metadata)
    write_json(root / "scene.json", validated)
    inventory_audit = replace(audit, status="VALIDATED") if audit is not None else None
    inventory = scene_to_content_inventory(
        validated, inventory_audit, audit_sha256=audit_file_hash
    )
    inventory_path = write_content_inventory(root / "content_inventory.json", inventory)
    result = {
        "status": "VALIDATED",
        "scene": str(root / "scene.json"),
        "report": report,
        "audit": audit_report,
        "content_inventory": str(inventory_path),
    }
    write_json(root / "reports" / "ingest.json", result)
    return result


__all__ = ["prepare_case", "ingest_scene", "validate_scene_proposal"]
