"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ppt_restore.contracts.models import AnalysisState
from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.platform.io import (
    read_case_manifest,
    read_registration,
    read_scene_any,
    write_case_manifest,
    write_json,
)
from ppt_restore.platform.provenance import sha256_file


def _backend(name, wps_pdf=None):
    from ppt_restore.rendering.renderers import (
        AutoRenderBackend,
        LibreOfficeBackend,
        PowerPointBackend,
        WpsBackend,
    )

    if name == "wps":
        return WpsBackend(exported_pdf=wps_pdf)
    if name == "auto":
        return AutoRenderBackend(wps_pdf=wps_pdf)
    return {
        "auto": AutoRenderBackend,
        "powerpoint": PowerPointBackend,
        "libreoffice": LibreOfficeBackend,
    }[name]()


def _set_manifest_state(case_dir, state, *, final=False, versions=None):
    manifest = read_case_manifest(case_dir)
    merged = dict(manifest.tool_versions)
    merged.update(versions or {})
    updated = replace(
        manifest,
        state=AnalysisState(state),
        final_verdict=AnalysisState(state) if final else manifest.final_verdict,
        tool_versions=merged,
    )
    write_case_manifest(case_dir, updated)


def _compile_scene(
    scene, case_root, output_path, *, blocks=None, render_strategy="hybrid_editable"
):
    """Compile the appropriate schema without silently downgrading v2."""

    if isinstance(scene, SceneSpecV2):
        from ppt_restore.rendering.scene_v2_compiler import SceneSpecCompiler

        if scene.state != "VALIDATED":
            raise ValueError(
                "SceneSpec v2 is not validated; run ingest and resolve NEEDS_REVIEW first"
            )
        canonical = Path(case_root) / "canonical.png"
        evidence = Path(case_root) / "evidence.json"
        if not canonical.is_file() or not evidence.is_file():
            raise ValueError("v2 build requires canonical.png and evidence.json")
        if scene.canonical_sha256 != sha256_file(canonical):
            raise ValueError("canonical_sha256 mismatch; re-run prepare and ingest")
        if scene.evidence_sha256 != sha256_file(evidence):
            raise ValueError("evidence_sha256 mismatch; re-run prepare and ingest")
        if (
            str((scene.metadata or {}).get("content_audit_status", "")).upper()
            == "VALIDATED"
        ):
            audit_report_path = Path(case_root) / "reports" / "content_audit.json"
            inventory_path = Path(case_root) / "content_inventory.json"
            if not audit_report_path.is_file() or not inventory_path.is_file():
                raise ValueError(
                    "validated multimodal SceneSpec requires content_audit.json and content_inventory.json"
                )
            try:
                audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ValueError("invalid content audit report: %s" % exc)
            if not bool(audit_report.get("valid", False)):
                raise ValueError("content audit requires review before build")
        from ppt_restore.pipeline.workflow import validate_scene_proposal
        from ppt_restore.platform.evidence import read_evidence

        checked, report = validate_scene_proposal(scene, read_evidence(evidence))
        if not report.get("valid", False):
            raise ValueError(
                "SceneSpec requires review before build: %s"
                % "; ".join(report.get("review_reasons", []))
            )
        return SceneSpecCompiler().compile(
            scene,
            output_path,
            canonical_path=Path(case_root) / "canonical.png",
            case_dir=case_root,
            render_strategy=render_strategy,
            strict_native=render_strategy == "strict_native",
            blocks=blocks,
        )
    raise ValueError("Only SceneSpec v2 is supported; submit a scene through ingest")


def _reconcile_content_after_build(result, case_root, output_path, *, blocks=None):
    """Run the deterministic model-output -> PPT DOM check when available."""

    from ppt_restore.quality.content_inventory import reconcile_inventory_with_pptx

    root = Path(case_root)
    inventory_path = root / "content_inventory.json"
    if not inventory_path.is_file() or not Path(output_path).is_file():
        return None
    report_path = root / "reports" / "content_dom_check.json"
    inventory = inventory_path
    if blocks is not None:
        scene = read_scene_any(root)
        if isinstance(scene, SceneSpecV2):
            from ppt_restore.rendering.scene_v2_compiler import _selected_nodes

            selected_ids = {node.id for node in _selected_nodes(scene, blocks)}
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["items"] = [
                item for item in inventory["items"] if item["node_id"] in selected_ids
            ]
    report = reconcile_inventory_with_pptx(
        inventory, output_path, report_path=report_path
    )
    report["scope"] = {
        "blocks": list(blocks) if blocks is not None else None,
        "full_slide": blocks is None,
    }
    write_json(report_path, report)
    result.content_inventory_path = str(inventory_path)
    result.content_dom_check_path = str(report_path)
    if not report.get("valid", False):
        missing = report.get("missing_critical", [])
        result.warnings.append(
            "critical content missing from PPT DOM: %s"
            % ", ".join(str(item.get("node_id", "")) for item in missing)
        )
    return report


def _verify(case_dir, pptx, renderer, wps_pdf=None):
    from ppt_restore.platform.provenance import build_provenance
    from ppt_restore.quality.gates import (
        GateDecision,
        GateEngine,
        QualityGateConfig,
        QualityStatus,
    )
    from ppt_restore.quality.metrics import MetricEngine

    case_root = Path(case_dir)
    canonical = case_root / "canonical.png"
    scene = read_scene_any(case_root) if (case_root / "scene.json").is_file() else None
    backend = _backend(renderer, wps_pdf=wps_pdf)
    rendered = backend.render(pptx, case_root / "renders" / renderer)
    report = (
        MetricEngine().evaluate(scene, canonical, rendered)
        if rendered.success
        else None
    )
    provenance = build_provenance(
        input_path=canonical if canonical.is_file() else None,
        pptx_path=pptx if Path(pptx).is_file() else None,
        scene_path=case_root / "scene.json"
        if (case_root / "scene.json").is_file()
        else None,
        renderer=rendered.backend,
        renderer_version=rendered.renderer_version,
    ).to_dict()
    registration = (
        read_registration(case_root)
        if (case_root / "registration.json").is_file()
        else None
    )
    strict_native = (
        not isinstance(scene, SceneSpecV2)
        or str((scene.metadata or {}).get("render_strategy", "hybrid_editable"))
        == "strict_native"
    )
    decision = GateEngine(QualityGateConfig(strict_native=strict_native)).evaluate(
        scene,
        report,
        rendered,
        pptx_path=pptx,
        input_path=canonical,
        registration=registration,
        provenance=provenance,
    )
    manifest_check = None
    content_dom_check = None
    if isinstance(scene, SceneSpecV2):
        from ppt_restore.quality.build_manifest import (
            find_build_manifest,
            validate_build_manifest,
        )
        from ppt_restore.quality.content_inventory import reconcile_inventory_with_pptx

        inventory_path = case_root / "content_inventory.json"
        if inventory_path.is_file() and Path(pptx).is_file():
            content_dom_check = reconcile_inventory_with_pptx(
                inventory_path,
                pptx,
                report_path=case_root / "reports" / "content_dom_check.json",
            )
        elif (
            str((scene.metadata or {}).get("content_audit_status", "")).upper()
            == "VALIDATED"
        ):
            content_dom_check = {
                "valid": False,
                "status": "NEEDS_REVIEW",
                "missing_critical": [],
                "missing": [
                    "content_inventory.json is required after a validated content audit"
                ],
            }

        found = find_build_manifest(case_root, pptx)
        if found is None:
            manifest_check = {
                "valid": False,
                "mismatches": ["content-addressed build manifest not found"],
            }
        else:
            manifest, _ = found
            manifest_check = validate_build_manifest(
                manifest,
                canonical_path=canonical,
                evidence_path=case_root / "evidence.json",
                scene_path=case_root / "scene.json",
                render_plan_path=case_root / "render_plan.json",
                pptx_path=pptx,
            )
        if not manifest_check.get("valid", False) and decision.status in (
            QualityStatus.PASS,
            QualityStatus.PREVERIFIED,
        ):
            decision = GateDecision(
                QualityStatus.NEEDS_REVIEW,
                reasons=["build manifest missing or invalid"] + list(decision.reasons),
                picture_count=decision.picture_count,
                metrics=decision.metrics,
                renderer=decision.renderer,
                threshold_version=decision.threshold_version,
                provenance=decision.provenance,
            )
        if (
            content_dom_check is not None
            and not content_dom_check.get("valid", False)
            and decision.status in (QualityStatus.PASS, QualityStatus.PREVERIFIED)
        ):
            decision = GateDecision(
                QualityStatus.NEEDS_REVIEW,
                reasons=["content inventory -> PPT DOM reconciliation failed"]
                + list(decision.reasons),
                picture_count=decision.picture_count,
                metrics=decision.metrics,
                renderer=decision.renderer,
                threshold_version=decision.threshold_version,
                provenance=decision.provenance,
            )
    payload = {
        "render": rendered.to_dict(),
        "metrics": report.to_dict() if report else None,
        "gate": decision.to_dict(),
        "provenance": provenance,
    }
    if manifest_check is not None:
        payload["build_manifest"] = manifest_check
    if content_dom_check is not None:
        payload["content_dom_check"] = content_dom_check
    write_json(case_root / "reports" / "verification.json", payload)
    _set_manifest_state(
        case_root,
        decision.status.value,
        final=True,
        versions={
            "renderer": rendered.backend,
            "renderer_version": rendered.renderer_version or "unknown",
        },
    )
    return payload, decision
