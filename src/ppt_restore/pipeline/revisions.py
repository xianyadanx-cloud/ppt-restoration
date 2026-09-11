"""Validate host-authored local edits without replacing the accepted scene."""

import copy
import json
from pathlib import Path

from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.pipeline.block_gate import (
    active_block,
    assert_build_allowed,
    read_block_gate,
)
from ppt_restore.platform.io import write_json
from ppt_restore.platform.provenance import sha256_file


def assert_ingest_scope(case_dir, proposal):
    """Full proposals cannot bypass the same local-edit boundary as revise."""
    root = Path(case_dir)
    gate = read_block_gate(root)
    if not gate or not (root / "scene.json").is_file():
        return
    original = SceneSpecV2.from_json((root / "scene.json").read_text(encoding="utf-8"))
    current = active_block(gate)
    before, after = original.to_dict(), proposal.to_dict()
    for key in ("canvas", "blocks", "canonical_sha256", "evidence_sha256"):
        if before.get(key) != after.get(key):
            raise ValueError(
                "local ingest cannot change %s; a new blueprint review is required"
                % key
            )
    locked_before = {
        n["id"]: n
        for n in before["nodes"]
        if current is None or n.get("block_id") != current
    }
    locked_after = {
        n["id"]: n
        for n in after["nodes"]
        if current is None or n.get("block_id") != current
    }
    if locked_before != locked_after:
        raise ValueError("ingest cannot modify another Block or global background")


def propose_revision(case_dir, patch_path, output):
    root = Path(case_dir).resolve()
    scene_path = root / "scene.json"
    patch = json.loads(Path(patch_path).read_text(encoding="utf-8"))
    if patch.get("base_scene_sha256") != sha256_file(scene_path):
        raise ValueError("stale revision: base_scene_sha256 does not match scene.json")
    gate = read_block_gate(root)
    block_id = patch.get("block_id")
    if not gate or active_block(gate) != block_id:
        raise ValueError("revision must target the active unapproved Block")
    assert_build_allowed(root, [block_id])
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    candidate = copy.deepcopy(scene)
    changes = patch.get("replacements", [])
    additions = patch.get("additions", [])
    removals = patch.get("removals", [])
    if not all(isinstance(value, list) for value in (changes, additions, removals)):
        raise ValueError("replacements, additions and removals must be arrays")
    if any(
        not isinstance(node, dict) or not isinstance(node.get("id"), str)
        for node in changes + additions
    ):
        raise ValueError("replacement and addition nodes require string ids")
    if not (changes or additions or removals):
        raise ValueError("revision requires node changes")
    nodes = {n["id"]: n for n in candidate["nodes"]}
    seen = set()
    for replacement in changes:
        node_id = replacement.get("id")
        if node_id in seen or node_id not in nodes:
            raise ValueError("duplicate or unknown replacement node")
        seen.add(node_id)
        if (
            nodes[node_id].get("block_id") != block_id
            or replacement.get("block_id") != block_id
        ):
            raise ValueError(
                "revision cannot modify another Block or global background"
            )
        nodes[node_id] = replacement
    for node_id in removals:
        if not isinstance(node_id, str) or node_id in seen or node_id not in nodes:
            raise ValueError("duplicate, conflicting or unknown removal node")
        seen.add(node_id)
        if nodes[node_id].get("block_id") != block_id:
            raise ValueError(
                "revision cannot remove another Block or global background"
            )
        del nodes[node_id]
    for addition in additions:
        node_id = addition.get("id")
        if not node_id or node_id in seen or node_id in nodes:
            raise ValueError("duplicate or conflicting addition node")
        if addition.get("block_id") != block_id:
            raise ValueError("new nodes must belong to the active Block")
        seen.add(node_id)
        nodes[node_id] = addition
    for node in nodes.values():
        parent = node.get("parent_id")
        if parent and parent not in nodes:
            raise ValueError("revision leaves an orphan node: %s" % node["id"])
        if node["id"] in seen and parent and nodes[parent].get("block_id") != block_id:
            raise ValueError(
                "revised nodes cannot attach to another Block or global background"
            )
    candidate["nodes"] = list(nodes.values())
    candidate["state"] = "PROPOSED"
    SceneSpecV2.from_dict(candidate)
    destination = Path(output).resolve()
    if destination == scene_path.resolve() or destination.exists():
        raise ValueError("revision output must be a new proposal file")
    write_json(destination, candidate)
    return {
        "status": "AUDIT_AND_INGEST_REQUIRED",
        "proposal": str(destination),
        "base_scene_sha256": patch["base_scene_sha256"],
        "block_id": block_id,
        "changes": {
            "replaced": [n["id"] for n in changes],
            "added": [n["id"] for n in additions],
            "removed": removals,
        },
        "instruction": "Re-read the source and submit a fresh content audit before ingest.",
    }
