"""Preserve each search's evidence and explicit host handoff."""

import json
import tempfile
from pathlib import Path

from ppt_restore.platform.io import write_json
from ppt_restore.platform.provenance import sha256_file


def new_run(case_dir):
    parent = Path(case_dir).resolve() / "candidates" / "runs"
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="search-", dir=str(parent)))


def save_result(run_dir, case_dir, proposal, payload, base_scene_sha256):
    root = Path(case_dir).resolve()
    destination = Path(run_dir) / "best_scene.json"
    write_json(destination, proposal)
    audit = Path(run_dir) / "content_audit.proposed.json"
    result = dict(
        payload,
        status="NEEDS_REVIEW",
        best_scene=str(destination),
        base_scene_sha256=base_scene_sha256,
        proposal_sha256=sha256_file(destination),
        input_hashes={
            name: sha256_file(root / name)
            for name in ("canonical.png", "evidence.json")
            if (root / name).is_file()
        },
        next_action="AUDIT_AND_INGEST_REQUIRED"
        if payload.get("improved")
        else "INSPECT_NO_IMPROVEMENT",
        required_read_files=[str(root / "canonical.png"), str(destination)],
        required_outputs=[str(audit)] if payload.get("improved") else [],
        after_audit_argv=[
            "pptrestore",
            "ingest",
            str(root),
            str(destination),
            "--content-audit",
            str(audit),
        ]
        if payload.get("improved")
        else None,
        automatic_approval=False,
    )
    write_json(Path(run_dir) / "optimization.json", result)
    return result


def pending_candidate(case_dir, block_id):
    """Discover a current intact proposal, never execute an unreviewed audit."""
    root = Path(case_dir).resolve()
    scene_hash = sha256_file(root / "scene.json")
    reports = sorted(
        (root / "candidates" / "runs").glob("search-*/optimization.json"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for path in reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if (
                report.get("block_id") != block_id
                or report.get("base_scene_sha256") != scene_hash
            ):
                continue
            if not report.get("improved"):
                return None
            proposal = path.parent / "best_scene.json"
            if not proposal.is_file() or sha256_file(proposal) != report.get(
                "proposal_sha256"
            ):
                return None
            if any(
                not (root / name).is_file() or sha256_file(root / name) != digest
                for name, digest in report.get("input_hashes", {}).items()
            ):
                return None
            audit = path.parent / "content_audit.proposed.json"
            return {
                "status": "CANDIDATE_AUDIT_REQUIRED",
                "action": "audit_candidate_then_ingest",
                "block_id": block_id,
                "read_files": [str(root / "canonical.png"), str(proposal), str(path)],
                "required_outputs": [str(audit)],
                "user_confirmation_required": False,
                "after_audit_argv": [
                    "pptrestore",
                    "ingest",
                    str(root),
                    str(proposal),
                    "--content-audit",
                    str(audit),
                ],
                "instruction": "Re-read the reference and audit this candidate before ingest. No approval is implied.",
            }
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return None
