"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json
from pathlib import Path

from ppt_restore.cli.services import (
    _compile_scene,
    _reconcile_content_after_build,
    _set_manifest_state,
    _verify,
)
from ppt_restore.contracts.models import AnalysisState
from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.pipeline.workflow import prepare_case
from ppt_restore.platform.io import read_scene_any


def run(args):
    output = Path(args.output)
    case_dir = Path(args.case_dir) if args.case_dir else output.with_suffix(".case")
    prepared = prepare_case(
        args.input,
        case_dir,
        page_index=args.page_index,
        primary_renderer=args.primary_renderer,
        ocr_mode=args.ocr,
    )
    registration = prepared["registration"]
    if registration.get("confidence", 0.0) < 0.90:
        payload = {
            "case_dir": str(case_dir),
            "status": "NEEDS_REVIEW",
            "reason": "registration confidence below 0.90",
            "registration": registration,
            "agent_request": prepared.get("agent_request"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    scene_path = case_dir / "scene.json"
    if not scene_path.is_file():
        payload = {
            "case_dir": str(case_dir),
            "status": "AWAITING_MULTIMODAL_SCENE_AND_AUDIT",
            "reason": "prepare completed; host Agent must submit pass-1 SceneSpec v2 and pass-2 content_audit.json before build",
            "agent_request": prepared.get("agent_request"),
            "scene_proposed": str(case_dir / "scene.proposed.json"),
            "content_audit_proposed": str(case_dir / "content_audit.proposed.json"),
            "required_passes": {
                "pass_1_scene_extraction": "scene.proposed.json",
                "pass_2_content_audit": "content_audit.proposed.json",
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    scene = read_scene_any(case_dir)
    if isinstance(scene, SceneSpecV2) and scene.state != "VALIDATED":
        payload = {
            "case_dir": str(case_dir),
            "status": "NEEDS_REVIEW",
            "reason": "SceneSpec v2 must be validated before build",
            "scene": str(scene_path),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    compatibility_warning = None
    if isinstance(scene, SceneSpecV2):
        audit_status = str(
            (scene.metadata or {}).get("content_audit_status", "")
        ).upper()
        if audit_status != "VALIDATED":
            compatibility_warning = "SceneSpec v2 has no validated pass-2 content audit"
            if not args.allow_missing_audit:
                payload = {
                    "case_dir": str(case_dir),
                    "status": "NEEDS_REVIEW",
                    "reason": compatibility_warning
                    + "; ingest with --content-audit or explicitly use --allow-missing-audit",
                    "scene": str(scene_path),
                    "content_audit_proposed": str(
                        case_dir / "content_audit.proposed.json"
                    ),
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 1
    from ppt_restore.pipeline.block_gate import assert_build_allowed, record_block_build

    assert_build_allowed(case_dir, args.blocks)
    build = _compile_scene(
        scene,
        case_dir,
        output,
        blocks=args.blocks,
        render_strategy=args.render_strategy,
    )
    _reconcile_content_after_build(build, case_dir, output, blocks=args.blocks)
    if args.blocks and not build.warnings:
        record_block_build(case_dir, args.blocks, output)
    elif args.blocks is None and not build.warnings:
        from ppt_restore.pipeline.host_tasks import record_full_build

        record_full_build(case_dir, output)
    _set_manifest_state(case_dir, AnalysisState.BUILT)
    if build.warnings:
        payload = {
            "case_dir": str(case_dir),
            "build": build.to_dict(),
            "status": "FAIL",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    verification, decision = _verify(
        case_dir, output, args.renderer, wps_pdf=args.wps_pdf
    )
    payload = {
        "case_dir": str(case_dir),
        "build": build.to_dict(),
        "verification": verification,
    }
    if compatibility_warning:
        payload["compatibility_warning"] = compatibility_warning
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if decision.status.value in ("PASS", "PREVERIFIED") else 1
