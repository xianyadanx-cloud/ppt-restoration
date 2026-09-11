"""Persistent, fail-closed Block review state for interactive restoration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Union

from ppt_restore.platform.provenance import sha256_file

PathLike = Union[str, Path]
STATUSES = ("PENDING", "BUILT", "APPROVED")


def _find_pptx_hash(value: Any) -> Optional[str]:
    """Find the build binding in a structured review report."""
    if isinstance(value, Mapping):
        direct = value.get("pptx_sha256")
        if isinstance(direct, str) and direct.strip():
            return direct.strip().lower()
        for child in value.values():
            found = _find_pptx_hash(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_pptx_hash(child)
            if found:
                return found
    return None


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scene_block_state(case_dir: PathLike) -> Optional[Dict[str, Any]]:
    """Return declared Block geometry and per-Block semantic hashes."""
    scene_path = Path(case_dir) / "scene.json"
    if not scene_path.is_file():
        return None
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    declared = scene.get("blocks", [])
    nodes = scene.get("nodes", [])
    if not isinstance(declared, list) or not declared:
        raise ValueError(
            "scene.json must declare blocks before Block gate initialization"
        )
    if not isinstance(nodes, list):
        raise ValueError("scene.json nodes must be an array")
    global_nodes = [
        node for node in nodes if isinstance(node, Mapping) and not node.get("block_id")
    ]
    blocks: Dict[str, Any] = {}
    for raw in declared:
        if not isinstance(raw, Mapping):
            raise ValueError("scene.json block entries must be objects")
        block_id = str(raw.get("id", "")).strip()
        if not block_id or block_id in blocks:
            raise ValueError("scene.json Block ids must be non-empty and unique")
        bbox = raw.get("bbox_norm")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("scene.json Block %s requires bbox_norm" % block_id)
        owned = [
            node
            for node in nodes
            if isinstance(node, Mapping) and str(node.get("block_id", "")) == block_id
        ]
        blocks[block_id] = {
            "bbox_norm": [float(value) for value in bbox],
            "semantic_sha256": _stable_hash(
                {
                    "block": raw,
                    "global_nodes": global_nodes,
                    "nodes": owned,
                    "canvas": scene.get("canvas"),
                    "source_binding": {
                        name: sha256_file(Path(case_dir) / name)
                        for name in ("canonical.png", "evidence.json")
                        if (Path(case_dir) / name).is_file()
                    },
                }
            ),
        }
    return {
        "path": str(scene_path.resolve()),
        "sha256": sha256_file(scene_path),
        "blocks": blocks,
    }


def _blocks_from_blueprint(data: Any):
    if isinstance(data, Mapping):
        data = data.get("blocks", data.get("regions", ()))
    if not isinstance(data, list) or not data:
        raise ValueError("block blueprint must contain a non-empty blocks array")
    blocks = []
    seen = set()
    for index, raw in enumerate(data, 1):
        if not isinstance(raw, Mapping):
            raise ValueError("block blueprint entries must be objects")
        block_id = str(raw.get("id", raw.get("block_id", "block_%d" % index))).strip()
        if not block_id or block_id in seen:
            raise ValueError("block blueprint ids must be non-empty and unique")
        seen.add(block_id)
        box = raw.get("bbox_norm", raw.get("box_norm", raw.get("bbox")))
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            raise ValueError("block %s requires bbox_norm" % block_id)
        blocks.append(
            {
                "id": block_id,
                "name": str(raw.get("name", raw.get("label", block_id))),
                "order": index,
                "bbox_norm": [float(value) for value in box],
                "status": "PENDING",
                "build_sha256": None,
                "build_scene_sha256": None,
                "approved_scene_sha256": None,
                "review_report": None,
                "review_sha256": None,
                "approved_at": None,
            }
        )
    return blocks


def init_block_gate(case_dir: PathLike, blueprint_path: PathLike) -> Dict[str, Any]:
    root, source = Path(case_dir), Path(blueprint_path)
    if not source.is_file():
        raise FileNotFoundError(str(source))
    data = json.loads(source.read_text(encoding="utf-8"))
    blocks = _blocks_from_blueprint(data)
    scene_state = _scene_block_state(root)
    if scene_state is not None:
        scene_blocks = scene_state["blocks"]
        blueprint_ids = [str(block["id"]) for block in blocks]
        if blueprint_ids != list(scene_blocks):
            raise ValueError("Block blueprint ids/order must match scene.json blocks")
        for block in blocks:
            scene_box = scene_blocks[str(block["id"])]["bbox_norm"]
            if any(
                abs(float(a) - float(b)) > 1e-6
                for a, b in zip(block["bbox_norm"], scene_box)
            ):
                raise ValueError(
                    "Block blueprint bbox must match scene.json for %s" % block["id"]
                )
    gate = {
        "schema_version": "1.0",
        "blueprint_path": str(source.resolve()),
        "blueprint_sha256": sha256_file(source),
        "blocks": blocks,
        "scene_path": scene_state["path"] if scene_state else None,
        "status": "AWAITING_BLOCK_BUILD",
    }
    _write(root / "block_gate.json", gate)
    return gate


def read_block_gate(case_dir: PathLike) -> Optional[Dict[str, Any]]:
    path = Path(case_dir) / "block_gate.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if str(data.get("schema_version")) != "1.0" or not isinstance(
        data.get("blocks"), list
    ):
        raise ValueError("invalid block_gate.json")
    return dict(data)


def _save(case_dir: PathLike, gate: Mapping[str, Any]) -> None:
    _write(Path(case_dir) / "block_gate.json", gate)


def active_block(gate: Mapping[str, Any]) -> Optional[str]:
    for block in gate.get("blocks", ()):
        if block.get("status") != "APPROVED":
            return str(block.get("id"))
    return None


def assert_build_allowed(
    case_dir: PathLike, requested_blocks: Optional[Sequence[str]]
) -> Optional[Dict[str, Any]]:
    gate = read_block_gate(case_dir)
    if gate is None:
        scene_path = Path(case_dir) / "scene.json"
        if scene_path.is_file():
            scene = json.loads(scene_path.read_text(encoding="utf-8"))
            if scene.get("nodes") or (
                scene.get("schema_version") == "2.0" and scene.get("blocks")
            ):
                raise ValueError(
                    "Block blueprint approval required before build; run pptrestore blueprint, "
                    "present it to the user, then run block-init after confirmation"
                )
        if requested_blocks:
            raise ValueError("block-init required before a Block build")
        return None
    blocks = list(gate["blocks"])
    approved = {str(item["id"]) for item in blocks if item.get("status") == "APPROVED"}
    scene_state = _scene_block_state(case_dir)
    if scene_state is not None:
        for item in blocks:
            block_id = str(item["id"])
            approved_hash = item.get("approved_scene_sha256")
            current_hash = (
                scene_state["blocks"].get(block_id, {}).get("semantic_sha256")
            )
            if (
                item.get("status") == "APPROVED"
                and approved_hash
                and current_hash != approved_hash
            ):
                raise ValueError(
                    "approved Block %s changed in scene.json; reinitialize and review it again"
                    % block_id
                )
    current = active_block(gate)
    if requested_blocks is None:
        if current is not None:
            raise ValueError("full build blocked; Block %s is not approved" % current)
        return gate
    wanted = {str(item) for item in requested_blocks}
    known = {str(item["id"]) for item in blocks}
    unknown = sorted(wanted - known)
    if unknown:
        raise ValueError("unknown Block(s): %s" % ", ".join(unknown))
    allowed = set(approved)
    if current:
        allowed.add(current)
    forbidden = sorted(wanted - allowed)
    if forbidden:
        raise ValueError(
            "Block build is sequential; approve %s before building %s"
            % (current, ", ".join(forbidden))
        )
    return gate


def record_block_build(
    case_dir: PathLike, requested_blocks: Sequence[str], pptx_path: PathLike
) -> Dict[str, Any]:
    gate = read_block_gate(case_dir)
    if gate is None:
        return {}
    digest = sha256_file(pptx_path)
    wanted = {str(item) for item in requested_blocks}
    blocks = list(gate["blocks"])
    current = active_block(gate)
    scene_state = _scene_block_state(case_dir)
    for block in blocks:
        if str(block["id"]) == current and str(block["id"]) in wanted:
            block_scene_hash = (
                scene_state["blocks"][current]["semantic_sha256"]
                if scene_state is not None
                else None
            )
            block.update(
                {
                    "status": "BUILT",
                    "build_path": str(Path(pptx_path).resolve()),
                    "build_sha256": digest,
                    "build_scene_sha256": block_scene_hash,
                    "review_report": None,
                    "review_sha256": None,
                    "approved_at": None,
                }
            )
    gate["blocks"] = blocks
    gate["status"] = (
        "AWAITING_USER_APPROVAL" if current in wanted else gate.get("status")
    )
    _save(case_dir, gate)
    return gate


def validate_v2_review(report, scene_path, block_id, pptx_sha256):
    """Shared report readiness check for next and explicit approval."""
    render = report.get("render", {})
    if (
        not isinstance(render, Mapping)
        or report.get("status") != "REVIEW_READY"
        or report.get("block_id") != block_id
        or report.get("scene_sha256") != sha256_file(scene_path)
        or render.get("success") is not True
        or render.get("backend") not in {"powerpoint", "wps", "libreoffice"}
        or render.get("pptx_sha256") != pptx_sha256
    ):
        raise ValueError(
            "v2 approval requires a current REVIEW_READY real-render report"
        )
    evidence, hashes = report.get("evidence", {}), report.get("evidence_sha256", {})
    if not isinstance(evidence, Mapping) or not isinstance(hashes, Mapping):
        raise ValueError("review evidence missing or changed")
    for name in ("reference", "rendered", "difference", "cumulative"):
        path = evidence.get(name)
        if (
            not isinstance(path, str)
            or not Path(path).is_file()
            or sha256_file(path) != hashes.get(name)
        ):
            raise ValueError("review evidence missing or changed: " + name)


def approve_block(
    case_dir: PathLike, block_id: str, review_report: PathLike, *, user_confirmed: bool
) -> Dict[str, Any]:
    if not user_confirmed:
        raise ValueError("Block approval requires explicit --user-confirmed")
    gate = read_block_gate(case_dir)
    if gate is None:
        raise ValueError("block gate is not initialized")
    current = active_block(gate)
    if str(block_id) != current:
        raise ValueError("only the active Block may be approved; active=%s" % current)
    report_path = Path(review_report)
    if not report_path.is_file():
        raise FileNotFoundError(str(report_path))
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Block review report must be valid JSON") from exc
    if not isinstance(report, Mapping):
        raise ValueError("Block review report must be a JSON object")
    blocks = list(gate["blocks"])
    target = next(item for item in blocks if str(item["id"]) == str(block_id))
    if target.get("status") != "BUILT" or not target.get("build_sha256"):
        raise ValueError("Block %s must be built before approval" % block_id)
    reviewed_hash = _find_pptx_hash(report)
    if not reviewed_hash:
        raise ValueError("Block review report must contain pptx_sha256")
    if reviewed_hash != str(target["build_sha256"]).lower():
        raise ValueError("Block review report does not match the latest Block build")
    build_path = target.get("build_path")
    if build_path and (
        not Path(build_path).is_file() or sha256_file(build_path) != reviewed_hash
    ):
        raise ValueError("reviewed PPTX is missing or changed; rebuild before approval")
    scene_path = Path(case_dir) / "scene.json"
    scene_data = (
        json.loads(scene_path.read_text(encoding="utf-8"))
        if scene_path.is_file()
        else {}
    )
    if scene_data.get("schema_version") == "2.0":
        validate_v2_review(report, scene_path, block_id, reviewed_hash)
    if report.get("status") in (
        "RENDER_FAILED",
        "FAILED",
        "NOT_FOR_ACCEPTANCE",
        "CONTENT_OR_NATIVE_REPAIR_REQUIRED",
    ):
        raise ValueError("failed review cannot approve a Block")
    if report.get("block_id") and str(report["block_id"]) != str(block_id):
        raise ValueError("review belongs to a different Block")
    scene_state = _scene_block_state(case_dir)
    if (
        scene_state
        and target.get("build_scene_sha256")
        != scene_state["blocks"][str(block_id)]["semantic_sha256"]
    ):
        raise ValueError("Block scene changed since build; rebuild before approval")
    if (
        report.get("scene_sha256")
        and sha256_file(Path(case_dir) / "scene.json") != report["scene_sha256"]
    ):
        raise ValueError("review scene is stale")
    target.update(
        {
            "status": "APPROVED",
            "review_report": str(report_path.resolve()),
            "review_sha256": sha256_file(report_path),
            "approved_scene_sha256": target.get("build_scene_sha256"),
            "approved_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
    )
    gate["blocks"] = blocks
    gate["status"] = (
        "ALL_BLOCKS_APPROVED" if active_block(gate) is None else "AWAITING_BLOCK_BUILD"
    )
    _save(case_dir, gate)
    return gate


__all__ = [
    "init_block_gate",
    "read_block_gate",
    "active_block",
    "assert_build_allowed",
    "record_block_build",
    "approve_block",
]
