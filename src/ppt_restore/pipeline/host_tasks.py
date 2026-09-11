"""Read-only, model-independent guidance for restoration hosts."""

import json
from pathlib import Path

from ppt_restore.pipeline.block_gate import (
    _scene_block_state,
    active_block,
    assert_build_allowed,
    read_block_gate,
)
from ppt_restore.platform.provenance import sha256_file


def _next_state(case_dir):
    root = Path(case_dir).resolve()
    result = {
        "case_dir": str(root),
        "automatic_approval": False,
        "required_strategy": "hybrid_editable",
        "allowed_block_ids": [],
    }
    if not (root / "canonical.png").is_file():
        return dict(
            result,
            status="PREPARE_REQUIRED",
            action="prepare",
            required_inputs=["source image or PDF"],
        )
    if not (root / "scene.json").is_file():
        return dict(
            result,
            status="EXTRACTION_REQUIRED",
            action="ingest",
            read_files=[
                str(root / name)
                for name in ("canonical.png", "evidence.json", "agent_request.json")
            ],
            required_outputs=["scene.proposed.json", "content_audit.proposed.json"],
        )
    scene = json.loads((root / "scene.json").read_text(encoding="utf-8"))
    result["required_strategy"] = scene.get("metadata", {}).get(
        "render_strategy", "hybrid_editable"
    )
    gate = read_block_gate(root)
    if gate is None:
        return dict(
            result,
            status="BLUEPRINT_CONFIRMATION_REQUIRED",
            action="block-init",
            read_files=[str(root / "scene.json")],
            user_confirmation_required=True,
        )
    current = active_block(gate)
    if current is None:
        assert_build_allowed(root, None)
        final = _final_task(root)
        if final:
            return dict(result, **final)
        return dict(
            result,
            status="FULL_BUILD_REQUIRED",
            action="build_then_verify",
            read_files=[str(root / "scene.json")],
        )
    block = next(b for b in gate["blocks"] if b["id"] == current)
    result["allowed_block_ids"] = [current]
    from ppt_restore.quality.optimization_runs import pending_candidate

    pending = pending_candidate(root, current)
    if pending:
        return dict(result, **pending)
    if block["status"] == "BUILT":
        build_path = block.get("build_path")
        if (
            not build_path
            or not Path(build_path).is_file()
            or sha256_file(build_path) != block["build_sha256"]
        ):
            return dict(
                result,
                status="BUILD_REQUIRED",
                action="build",
                block_id=current,
                instruction="The latest build is missing or changed; rebuild before review.",
            )
        if block.get("build_scene_sha256"):
            state = _scene_block_state(root)
            if (
                state["blocks"].get(current, {}).get("semantic_sha256")
                != block["build_scene_sha256"]
            ):
                return dict(
                    result,
                    status="BUILD_REQUIRED",
                    action="build",
                    block_id=current,
                    instruction="The active Block changed after ingest; rebuild before requesting review.",
                )
        report_path = root / "reviews" / current / block["build_sha256"] / "review.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if (
                report.get("scene_sha256") == sha256_file(root / "scene.json")
                and report.get("pptx_sha256") == block["build_sha256"]
            ):
                build_path = block.get("build_path")
                if (
                    not build_path
                    or not Path(build_path).is_file()
                    or sha256_file(build_path) != block["build_sha256"]
                ):
                    return dict(
                        result,
                        status="BUILD_REQUIRED",
                        action="build",
                        block_id=current,
                        instruction="The reviewed build is missing or changed; rebuild before review.",
                    )
                ready = report.get("status") == "REVIEW_READY"
                if (
                    ready
                    and json.loads(
                        (root / "scene.json").read_text(encoding="utf-8")
                    ).get("schema_version")
                    == "2.0"
                ):
                    from ppt_restore.pipeline.block_gate import validate_v2_review

                    try:
                        validate_v2_review(
                            report, root / "scene.json", current, block["build_sha256"]
                        )
                    except (ValueError, OSError) as exc:
                        return dict(
                            result,
                            status="REVIEW_REQUIRED",
                            action="review",
                            block_id=current,
                            read_files=[str(report_path)],
                            instruction="Regenerate review evidence before presenting it for approval: "
                            + str(exc),
                        )
                content_failure = (
                    report.get("status") == "CONTENT_OR_NATIVE_REPAIR_REQUIRED"
                )
                return dict(
                    result,
                    status="AWAITING_VISUAL_REVIEW"
                    if ready
                    else "CONTENT_REPAIR_REQUIRED"
                    if content_failure
                    else "RENDER_REPAIR_REQUIRED",
                    action="inspect_evidence_then_request_user_review"
                    if ready
                    else "revise_audit_ingest_then_build"
                    if content_failure
                    else "repair_renderer_then_review",
                    block_id=current,
                    read_files=[str(report_path)],
                    user_confirmation_required=ready,
                    instruction="Inspect both source and rendered images. Repair differences before requesting approval; never infer approval from metrics.",
                )
    return dict(
        result,
        status="REVIEW_REQUIRED" if block["status"] == "BUILT" else "BUILD_REQUIRED",
        action="review" if block["status"] == "BUILT" else "build",
        block_id=current,
        latest_build_sha256=block.get("build_sha256"),
        read_files=[str(root / "scene.json"), str(root / "canonical.png")],
        user_confirmation_required=block["status"] == "BUILT",
    )


def next_task(case_dir):
    """Return argv arrays, never shell strings or automatic user approvals."""
    task = _next_state(case_dir)
    root = Path(task["case_dir"])
    status = task["status"]
    command = None
    if status == "EXTRACTION_REQUIRED":
        command = [
            "ingest",
            str(root),
            str(root / "scene.proposed.json"),
            "--content-audit",
            str(root / "content_audit.proposed.json"),
        ]
    elif status == "BLUEPRINT_CONFIRMATION_REQUIRED":
        command = ["blueprint", str(root)]
        task["required_outputs"] = [
            "block_map.png",
            "blueprint.json",
            "user-confirmed block map",
        ]
    elif status in {"BUILD_REQUIRED", "FULL_BUILD_REQUIRED"}:
        scene_hash = sha256_file(root / "scene.json")[:16]
        output = root / "deliverables" / ("build-" + scene_hash + ".pptx")
        index = 1
        while output.exists():
            output = output.with_name("build-%s-%d.pptx" % (scene_hash, index))
            index += 1
        command = [
            "build",
            str(root),
            "--output",
            str(output),
            "--render-strategy",
            task["required_strategy"],
        ]
        if task.get("block_id"):
            gate = read_block_gate(root)
            included = [
                b["id"] for b in gate["blocks"] if b["status"] == "APPROVED"
            ] + [task["block_id"]]
            command += ["--blocks"] + included
            task["build_block_ids"] = included
        task["required_outputs"] = [str(output)]
    elif status == "VERIFY_REQUIRED":
        command = ["verify", str(root), task["pptx_path"]]
    elif status == "REVIEW_REQUIRED":
        command = ["review", str(root), "--block", task["block_id"]]
        task["user_confirmation_required"] = False
    task["command_argv"] = ["pptrestore"] + command if command else None
    task["after_action"] = ["pptrestore", "next", str(root)]
    return task


def record_full_build(case_dir, pptx_path):
    """Record only successful full builds, never infer one from a partial PPT."""
    from ppt_restore.platform.io import write_json

    root = Path(case_dir).resolve()
    record = {
        "pptx_path": str(Path(pptx_path).resolve()),
        "pptx_sha256": sha256_file(pptx_path),
        "inputs": {
            name: sha256_file(root / name)
            for name in ("scene.json", "canonical.png", "evidence.json")
            if (root / name).is_file()
        },
    }
    write_json(root / "reports" / "full_build.json", record)


def _final_task(root):
    path = root / "reports" / "full_build.json"
    if not path.is_file():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    pptx = Path(record["pptx_path"])
    if not pptx.is_file() or sha256_file(pptx) != record["pptx_sha256"]:
        return None
    if any(
        not (root / name).is_file() or sha256_file(root / name) != digest
        for name, digest in record["inputs"].items()
    ):
        return None
    result = {
        "status": "VERIFY_REQUIRED",
        "action": "verify",
        "pptx_path": str(pptx),
        "read_files": [str(path)],
    }
    verification = root / "reports" / "verification.json"
    if not verification.is_file():
        return result
    report = json.loads(verification.read_text(encoding="utf-8"))
    provenance = report.get("provenance", {})
    if (
        provenance.get("pptx_sha256") != record["pptx_sha256"]
        or provenance.get("scene_sha256") != record["inputs"].get("scene.json")
        or provenance.get("input_sha256") != record["inputs"].get("canonical.png")
    ):
        return result
    status = report.get("gate", {}).get("status")
    result["read_files"].append(str(verification))
    if status in {"PASS", "PREVERIFIED"}:
        result.update(
            status="FINAL_USER_REVIEW_REQUIRED",
            action="present_final_evidence",
            verification_status=status,
            user_confirmation_required=True,
            instruction="Present the final PPT and true-render comparison. PREVERIFIED is not PowerPoint PASS; never infer final user acceptance.",
        )
    else:
        result.update(
            status="FINAL_REPAIR_REQUIRED",
            action="inspect_verification_failure",
            instruction="Inspect verification reasons. Do not lower thresholds or modify approved blocks without renewed review.",
        )
    return result
