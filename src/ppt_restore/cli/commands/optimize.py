"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json
from pathlib import Path

from ppt_restore.cli.services import _backend
from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.platform.io import read_scene_any
from ppt_restore.platform.provenance import sha256_file


def run(args):
    from ppt_restore.pipeline.block_gate import assert_build_allowed

    gate = assert_build_allowed(args.case_dir, [args.block])
    if gate and any(
        b["id"] == args.block and b["status"] == "APPROVED" for b in gate["blocks"]
    ):
        raise ValueError("approved blocks are locked for optimization")
    from ppt_restore.quality.optimizer import Optimizer

    case_root = Path(args.case_dir)
    scene = read_scene_any(case_root)
    from ppt_restore.quality.optimization_runs import new_run, save_result

    base_scene_sha256 = sha256_file(case_root / "scene.json")
    run_root = new_run(case_root)
    canonical = case_root / "canonical.png"
    backend = _backend(args.renderer)
    if getattr(backend, "name", None) == "auto":
        backend = next(
            (
                item
                for item in backend.backends
                if item.name in {"powerpoint", "libreoffice"} and item.available
            ),
            None,
        )
        if backend is None:
            raise ValueError("no automatic real renderer is available for optimization")
    optimizer = Optimizer(
        max_rounds=args.max_rounds, max_candidates=args.max_candidates
    )
    from ppt_restore.quality.render_probe import run_render_probe

    probe = run_render_probe(backend, case_root / "renderer_probes")
    if not probe["automatic_optimization_allowed"]:
        raise ValueError("renderer probe failed; inspect " + probe["report_path"])
    from ppt_restore.quality.visual_objective import FixedRegionObjective

    region = next(
        (b for b in scene.blocks if str(b.get("id")) == str(args.block)), None
    )
    if region is None:
        raise ValueError("optimization requires an explicit fixed reference block")
    width, height = (
        float(scene.canvas["width_px"]),
        float(scene.canvas["height_px"]),
    )
    text_boxes = []
    for node in scene.nodes:
        if node.block_id == args.block and node.kind in {
            "text",
            "table",
            "badge",
            "kpi_card",
        }:
            x, y, w, h = node.bbox_px
            text_boxes.append(
                [
                    x * 1000 / width,
                    y * 1000 / height,
                    w * 1000 / width,
                    h * 1000 / height,
                ]
            )
    fixed_objective = FixedRegionObjective(canonical, region["bbox_norm"], text_boxes)
    from ppt_restore.quality.cache_context import visual_cache_context
    from ppt_restore.rendering.renderers import _renderer_version

    executable = getattr(backend, "executable", None)
    optimizer.cache_context = visual_cache_context(
        canonical,
        {
            "requested": args.renderer,
            "backend": getattr(backend, "name", None),
            "executable": executable,
            "version": _renderer_version(executable) if executable else None,
        },
        {
            "version": fixed_objective.version,
            "block_id": args.block,
            "reference_box_px": list(fixed_objective.box),
        },
    )
    allowed_blocks = [args.block]
    if gate:
        allowed_blocks = [
            b["id"] for b in gate["blocks"] if b["status"] == "APPROVED"
        ] + [args.block]

    def render_candidate(candidate, block_id):
        digest = optimizer.scene_hash(candidate)
        root = run_root / digest
        pptx = root / "candidate.pptx"
        if isinstance(candidate, SceneSpecV2):
            from ppt_restore.rendering.scene_v2_compiler import SceneSpecCompiler

            candidate = SceneSpecV2.from_dict(candidate.to_dict())
            build = SceneSpecCompiler().compile(
                candidate,
                pptx,
                canonical_path=canonical,
                blocks=allowed_blocks,
                strict_native=candidate.metadata.get("render_strategy")
                == "strict_native",
            )
            from ppt_restore.quality.content_inventory import (
                reconcile_inventory_with_pptx,
                scene_to_content_inventory,
            )

            inventory = scene_to_content_inventory(candidate)
            ids = {
                n.id
                for n in candidate.nodes
                if n.block_id in allowed_blocks or not n.block_id
            }
            inventory["items"] = [
                item for item in inventory["items"] if item["node_id"] in ids
            ]
            check = reconcile_inventory_with_pptx(inventory, pptx)
            if check["missing"]:
                raise ValueError("candidate loses source content")
        else:
            raise ValueError("Optimization requires SceneSpec v2")
        if build.warnings:
            raise ValueError("candidate build failed: " + "; ".join(build.warnings))
        rendered = backend.render(pptx, root / "render")
        if not rendered.success:
            raise ValueError(rendered.error or "render failed")
        if rendered.backend not in {
            "powerpoint",
            "libreoffice",
        } or rendered.pptx_sha256 != sha256_file(pptx):
            raise ValueError(
                "automatic optimization requires a hash-bound real automatic renderer"
            )
        if not rendered.images:
            raise ValueError("renderer produced no image")
        return fixed_objective.evaluate(rendered.images[0])

    def visual_loss(report):
        return report["loss"]

    priority_nodes = []
    priority_source = None
    if gate:
        target = next(b for b in gate["blocks"] if b["id"] == args.block)
        review_path = (
            case_root
            / "reviews"
            / args.block
            / str(target.get("build_sha256"))
            / "review.json"
        )
        if review_path.is_file():
            review = json.loads(review_path.read_text(encoding="utf-8"))
            if (
                review.get("scene_sha256") == sha256_file(case_root / "scene.json")
                and review.get("pptx_sha256") == target.get("build_sha256")
                and review.get("status") == "REVIEW_READY"
            ):
                issues = sorted(
                    review.get("issues", []),
                    key=lambda issue: (
                        issue.get("priority", 99),
                        -issue.get("measurement", {}).get("mean_absolute_rgb_error", 0),
                    ),
                )
                priority_nodes = list(
                    dict.fromkeys(
                        issue["node_id"]
                        for issue in issues
                        if issue.get("node_id") and issue.get("block_id") == args.block
                    )
                )
                priority_source = str(review_path)
    result = optimizer.optimize(
        scene,
        args.block,
        visual_loss,
        render=render_candidate,
        priority_node_ids=priority_nodes,
    )
    proposal = (
        result.scene.to_dict()
        if hasattr(result.scene, "to_dict")
        else dict(result.scene)
    )
    if isinstance(scene, SceneSpecV2):
        proposal["state"] = "PROPOSED"
    payload = result.to_dict()
    payload["cache_context"] = optimizer.cache_context
    payload["candidate_priority"] = {
        "review": priority_source,
        "node_ids": priority_nodes,
    }
    payload["objective_version"] = (
        fixed_objective.version if fixed_objective else "legacy-metrics"
    )
    payload.update(
        {
            "renderer": getattr(backend, "name", args.renderer),
            "note": "Optimization never grants PASS; audit and ingest improved proposals before build and review.",
        }
    )
    payload = save_result(run_root, case_root, proposal, payload, base_scene_sha256)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
