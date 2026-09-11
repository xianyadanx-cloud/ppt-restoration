"""Hash-bound Block evidence; a review never grants visual acceptance."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageChops

from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.pipeline.block_gate import (
    _scene_block_state,
    assert_build_allowed,
    read_block_gate,
)
from ppt_restore.platform.io import read_scene_any, write_json
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.content_inventory import (
    reconcile_inventory_with_pptx,
    scene_to_content_inventory,
)
from ppt_restore.quality.metrics import calculate_edge_f1, calculate_ssim


def review_block(case_dir, block_id, backend, pptx=None):
    root = Path(case_dir).resolve()
    gate = read_block_gate(root)
    if not gate:
        raise ValueError("initialize the confirmed blueprint before review")
    assert_build_allowed(root, [block_id])
    block = next((b for b in gate["blocks"] if b["id"] == block_id), None)
    if not block or not block.get("build_sha256"):
        raise ValueError("block must be built before review")
    scene_state = _scene_block_state(root)
    if (
        scene_state
        and block.get("build_scene_sha256")
        != scene_state["blocks"][block_id]["semantic_sha256"]
    ):
        raise ValueError("scene changed since Block build; rebuild before review")
    path = pptx or block.get("build_path")
    if not path:
        raise ValueError("build record has no PPTX path; rebuild the block")
    digest = sha256_file(path)
    if digest != block["build_sha256"]:
        raise ValueError("PPTX does not match the latest Block build")
    out = root / "reviews" / block_id / digest
    out.mkdir(parents=True, exist_ok=True)
    rendered = backend.render(path, out / "render")
    report = {
        "status": "RENDER_FAILED",
        "block_id": block_id,
        "pptx_sha256": digest,
        "scene_sha256": sha256_file(root / "scene.json"),
        "render": rendered.to_dict(),
        "user_approval": "PENDING",
        "issues": [],
        "content_preservation": "NOT_CHECKED",
        "native_editability": "NOT_CHECKED",
        "visual_match": "NOT_ACCEPTED",
    }
    scene = read_scene_any(root)
    if isinstance(scene, SceneSpecV2):
        selected_ids = {n.id for n in scene.nodes if n.block_id == block_id}
        inventory = scene_to_content_inventory(scene)
        inventory["items"] = [
            item for item in inventory["items"] if item["node_id"] in selected_ids
        ]
        report["content_preservation"] = reconcile_inventory_with_pptx(inventory, path)
    with zipfile.ZipFile(path) as package:
        pictures = sum(
            len(
                ElementTree.fromstring(package.read(name)).findall(
                    ".//{http://schemas.openxmlformats.org/presentationml/2006/main}pic"
                )
            )
            for name in package.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
    report["native_editability"] = {
        "picture_count": pictures,
        "strict_native": pictures == 0,
        "claim": "picture count does not prove native table/chart semantics",
    }
    if rendered.success and rendered.pptx_sha256 != digest:
        report["render"]["error"] = "render provenance does not match the reviewed PPTX"
    elif (
        rendered.success
        and rendered.images
        and rendered.backend in {"powerpoint", "wps", "libreoffice"}
    ):
        with Image.open(root / "canonical.png") as source:
            source = source.convert("RGB")
        with Image.open(rendered.images[0]) as actual:
            actual = actual.convert("RGB").resize(source.size)
        l, t, w, h = block["bbox_norm"]
        box = tuple(
            round(v)
            for v in (
                l * source.width / 1000,
                t * source.height / 1000,
                (l + w) * source.width / 1000,
                (t + h) * source.height / 1000,
            )
        )
        ref, got = source.crop(box), actual.crop(box)
        ref.save(out / "reference.png")
        got.save(out / "rendered.png")
        ImageChops.difference(ref, got).save(out / "difference.png")
        actual.save(out / "cumulative.png")
        report.update(
            status="REVIEW_READY",
            metrics={
                "ssim": calculate_ssim(got, ref),
                "edge_f1": calculate_edge_f1(got, ref),
            },
            evidence={
                name: str(out / (name + ".png"))
                for name in ("reference", "rendered", "difference", "cumulative")
            },
        )
        report["issues"].append(
            {
                "block_id": block_id,
                "node_id": None,
                "category": "VISUAL_REVIEW_REQUIRED",
                "detection_source": "render_comparison",
                "confidence": None,
                "allowed_fields": ["bbox_px", "style"],
                "evidence": report["evidence"],
            }
        )
        if isinstance(scene, SceneSpecV2):
            from ppt_restore.quality.issue_localization import localize_issues

            report["issues"] = (
                localize_issues(
                    scene, block_id, source, actual, out, report["scene_sha256"], digest
                )
                + report["issues"]
            )
    expected_pictures = sum(node.kind == "image" for node in scene.nodes)
    strict_native = scene.metadata.get("render_strategy") == "strict_native"
    if (
        (strict_native and pictures > 0)
        or pictures > expected_pictures
        or isinstance(report["content_preservation"], dict)
        and report["content_preservation"]["missing"]
    ):
        report["status"] = "CONTENT_OR_NATIVE_REPAIR_REQUIRED"
    report["evidence_sha256"] = {
        name: sha256_file(path) for name, path in report.get("evidence", {}).items()
    }
    write_json(out / "review.json", report)
    return report
