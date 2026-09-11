"""Synthetic mechanical renderer checks, not screenshot fidelity acceptance."""

import tempfile
from pathlib import Path

from PIL import Image, ImageStat

from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.platform.io import write_json
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.rendering.renderers import check_pdf_cjk_preservation
from ppt_restore.rendering.scene_v2_compiler import SceneSpecCompiler


def run_render_probe(backend, output_dir):
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="probe-", dir=str(root)))
    nodes = (
        SceneNode(
            "chinese",
            "text",
            "title",
            (20, 20, 940, 100),
            payload={"text": "季度目标 中文测试 84%"},
            style={"font_family": "Heiti SC", "font_size_pt": 28, "color": "#000000"},
        ),
        SceneNode(
            "gradient",
            "shape",
            "decoration",
            (20, 180, 400, 100),
            style={
                "gradient_stops": [[0, "#FF0000"], [1, "#0000FF"]],
                "gradient_angle": 0,
            },
        ),
        SceneNode(
            "table",
            "table",
            "body",
            (500, 180, 400, 100),
            payload={
                "cells": [["目标", "84%"], ["完成", "100%"]],
                "row_bg_colors": ["#00FF00", "#FFFF00"],
            },
            style={"font_family": "Heiti SC", "font_size_pt": 18},
        ),
        SceneNode(
            "polygon",
            "shape",
            "decoration",
            (20, 340, 200, 160),
            payload={
                "shape_type": "polygon",
                "points": [[0, 160], [100, 0], [200, 160]],
            },
            style={"fill": "#00FFFF"},
        ),
    )
    scene = SceneSpecV2(
        "2.0",
        "0" * 64,
        "0" * 64,
        {"width_px": 1000, "height_px": 600},
        nodes,
        state="VALIDATED",
    )
    pptx = run / "probe.pptx"
    build = SceneSpecCompiler().compile(scene, pptx, strict_native=True)
    rendered = backend.render(pptx, run / "render") if not build.warnings else None
    checks = {
        "build": not build.warnings,
        "real_render": bool(
            rendered
            and rendered.success
            and rendered.backend in {"powerpoint", "libreoffice"}
            and rendered.pptx_sha256 == sha256_file(pptx)
        ),
    }
    evidence = {}
    if checks["real_render"] and rendered.images:
        with Image.open(rendered.images[0]) as image:
            image = image.convert("RGB").resize((1000, 600))

        def sample(x, y):
            return ImageStat.Stat(image.crop((x - 3, y - 3, x + 3, y + 3))).mean

        left, right = sample(60, 230), sample(380, 230)
        checks["gradient_direction"] = (
            left[0] > left[2] + 100 and right[2] > right[0] + 100
        )
        green, yellow = sample(510, 190), sample(510, 270)
        checks["table_cells"] = (
            green[1] > 200 and green[0] < 60 and yellow[0] > 200 and yellow[1] > 200
        )
        inside, outside = sample(120, 440), sample(30, 350)
        checks["freeform_geometry"] = (
            inside[0] < 60
            and inside[1] > 200
            and inside[2] > 200
            and min(outside) > 230
        )
        gray = image.crop((20, 20, 960, 120)).convert("L")
        dark = sum(count for value, count in enumerate(gray.histogram()) if value < 100)
        checks["text_visible"] = dark > 1000
        pdfs = list((run / "render").rglob("probe.pdf"))
        cjk = (
            check_pdf_cjk_preservation(pptx, pdfs[0])
            if len(pdfs) == 1
            else {"status": "UNVERIFIED"}
        )
        checks["chinese_text_preserved"] = cjk["status"] == "TEXT_PRESERVED"
        evidence = {
            "image": rendered.images[0],
            "cjk": cjk,
            "gradient_samples": [left, right],
        }
    passed = len(checks) == 7 and all(checks.values())
    report = {
        "version": "1",
        "status": "PROBE_PASSED" if passed else "PROBE_FAILED",
        "automatic_optimization_allowed": passed,
        "checks": checks,
        "evidence": evidence,
        "render": rendered.to_dict() if rendered else None,
        "build_warnings": build.warnings,
        "pptx_sha256": sha256_file(pptx),
        "report_path": str(run / "probe.json"),
        "claim": "Synthetic feature checks only; not real-image fidelity or user approval.",
    }
    write_json(run / "probe.json", report)
    return report
