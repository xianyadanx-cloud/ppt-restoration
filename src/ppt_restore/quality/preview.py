"""Host self-check: compile a *proposed* scene, render it, and show where it differs.

``pptrestore preview`` is the render -> diff -> repair loop for the host agent
before pass 2.  It never ingests, approves or edits anything: it only writes
images and a JSON report under ``previews/`` so the host can look at its own
output next to canonical.png and fix the largest discrepancies.  Pixels say
*where* the result differs, not *why*; the host must re-read the source.
"""

import dataclasses
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

from ppt_restore.contracts.schema_v2 import SceneSpecV2, scene_sha256
from ppt_restore.platform.io import write_json
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality import metrics as M

GRID_COLS, GRID_ROWS = 16, 9


def _norm_box(box, width, height):
    x0, y0, x1, y1 = box
    return [
        round(x0 * 1000.0 / width, 1),
        round(y0 * 1000.0 / height, 1),
        round((x1 - x0) * 1000.0 / width, 1),
        round((y1 - y0) * 1000.0 / height, 1),
    ]


def _mean_rgb(image):
    return [round(v) for v in ImageStat.Stat(image.convert("RGB")).mean[:3]]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb)


def _error(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean[:3]) / (3 * 255.0)


def _ink_fraction(image):
    mask = M._detail_mask(image)
    return ImageStat.Stat(mask).mean[0] / 255.0


def _overlay(source, render):
    """Faded source with red where the render differs."""
    diff = ImageChops.difference(source, render).convert("L").filter(ImageFilter.GaussianBlur(1))
    diff = diff.point(lambda v: 0 if v < 24 else min(255, 64 + v * 2))
    base = Image.blend(source.convert("L").convert("RGB"), Image.new("RGB", source.size, "white"), 0.55)
    red = Image.new("RGB", source.size, (230, 0, 0))
    return Image.composite(red, base, diff)


def _labelled_row(images, labels):
    pad = 28
    width = sum(i.width for i in images) + 8 * (len(images) - 1)
    canvas = Image.new("RGB", (width, images[0].height + pad), "white")
    draw = ImageDraw.Draw(canvas)
    x = 0
    for image, label in zip(images, labels):
        canvas.paste(image, (x, pad))
        draw.text((x + 6, 6), label, fill="black")
        x += image.width + 8
    return canvas


def node_regions(scene, source, render):
    width, height = float(scene.canvas["width_px"]), float(scene.canvas["height_px"])
    rows = []
    for index, node in enumerate(scene.nodes):
        x, y, w, h = node.bbox_px
        box = (
            max(0, int(round(x))),
            max(0, int(round(y))),
            min(source.width, int(round(x + w))),
            min(source.height, int(round(y + h))),
        )
        if box[2] - box[0] < 2 or box[3] - box[1] < 2:
            continue
        ref, got = source.crop(box), render.crop(box)
        rows.append(
            {
                "node_id": node.id,
                "kind": node.kind,
                "paint_index": index,
                "bbox_norm": _norm_box(box, width, height),
                "mean_abs_error": round(_error(ref, got), 4),
                "source_mean": _hex(_mean_rgb(ref)),
                "render_mean": _hex(_mean_rgb(got)),
                "source_ink": round(_ink_fraction(ref), 3),
                "render_ink": round(_ink_fraction(got), 3),
            }
        )
    rows.sort(key=lambda r: -r["mean_abs_error"] * (r["bbox_norm"][2] * r["bbox_norm"][3]) ** 0.5)
    return rows


def grid_regions(scene, source, render):
    width, height = source.size
    covered = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(covered)
    for node in scene.nodes:
        x, y, w, h = node.bbox_px
        draw.rectangle([x, y, x + w, y + h], fill=255)
    cells = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            box = (
                col * width // GRID_COLS,
                row * height // GRID_ROWS,
                (col + 1) * width // GRID_COLS,
                (row + 1) * height // GRID_ROWS,
            )
            ref, got = source.crop(box), render.crop(box)
            cells.append(
                {
                    "cell": [col, row],
                    "bbox_norm": _norm_box(box, width, height),
                    "mean_abs_error": round(_error(ref, got), 4),
                    "source_mean": _hex(_mean_rgb(ref)),
                    "render_mean": _hex(_mean_rgb(got)),
                    "source_ink": round(_ink_fraction(ref), 3),
                    "render_ink": round(_ink_fraction(got), 3),
                    "node_coverage": round(ImageStat.Stat(covered.crop(box)).mean[0] / 255.0, 3),
                }
            )
    return cells


def _merge_cells(cells, predicate):
    """Group adjacent flagged grid cells into rectangles (bbox_norm)."""
    flagged = {tuple(c["cell"]) for c in cells if predicate(c)}
    by = {tuple(c["cell"]): c for c in cells}
    seen, groups = set(), []
    for start in sorted(flagged):
        if start in seen:
            continue
        stack, members = [start], []
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            members.append((cx, cy))
            for nxt in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if nxt in flagged and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        boxes = [by[m]["bbox_norm"] for m in members]
        left = min(b[0] for b in boxes)
        top = min(b[1] for b in boxes)
        right = max(b[0] + b[2] for b in boxes)
        bottom = max(b[1] + b[3] for b in boxes)
        error = sum(by[m]["mean_abs_error"] for m in members) / len(members)
        groups.append(
            {
                "bbox_norm": [round(left, 1), round(top, 1), round(right - left, 1), round(bottom - top, 1)],
                "cells": len(members),
                "mean_abs_error": round(error, 4),
            }
        )
    groups.sort(key=lambda g: -g["mean_abs_error"] * g["cells"])
    return groups


def _attach_nodes(cells, scene):
    width, height = float(scene.canvas["width_px"]), float(scene.canvas["height_px"])
    boxes = []
    for node in scene.nodes:
        x, y, w, h = node.bbox_px
        boxes.append((node.id, x * 1000 / width, y * 1000 / height, (x + w) * 1000 / width, (y + h) * 1000 / height))
    for cell in cells:
        l, t, w, h = cell["bbox_norm"]
        # paint order: later ids are drawn on top
        cell["nodes_here"] = [
            i for i, x0, y0, x1, y1 in boxes if x0 < l + w and x1 > l and y0 < t + h and y1 > t
        ][-6:]


def _save_region_crops(source, render, regions, out_dir, scale=2, limit=6):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    width, height = source.size
    for k, region in enumerate(regions[:limit]):
        l, t, w, h = region["bbox_norm"]
        # one grid cell of context on every side
        box = (
            max(0, int((l - w) * width / 1000)),
            max(0, int((t - h) * height / 1000)),
            min(width, int((l + 2 * w) * width / 1000)),
            min(height, int((t + 2 * h) * height / 1000)),
        )
        ref, got = source.crop(box), render.crop(box)
        factor = max(1, min(scale, int(1400 / max(1, 2 * ref.width))))
        size = (ref.width * factor, ref.height * factor)
        row = _labelled_row(
            [ref.resize(size, Image.LANCZOS), got.resize(size, Image.LANCZOS)],
            ["source %s" % region["bbox_norm"], "render"],
        )
        path = out_dir / ("region_%02d.png" % (k + 1))
        row.save(path)
        region["crop"] = str(path)
        paths.append(str(path))
    return paths


def preview_scene(case_dir, proposed_path, output_dir=None, renderer="libreoffice", backend=None):
    from ppt_restore.pipeline.workflow import validate_scene_proposal
    from ppt_restore.platform.evidence import read_evidence
    from ppt_restore.rendering.scene_v2_compiler import SceneSpecCompiler

    root = Path(case_dir).resolve()
    canonical = root / "canonical.png"
    scene = SceneSpecV2.from_json(Path(proposed_path).read_text(encoding="utf-8"))
    checked, structural = validate_scene_proposal(scene, read_evidence(root / "evidence.json"))
    if scene.evidence_sha256 != sha256_file(root / "evidence.json"):
        raise ValueError("evidence_sha256 mismatch; preview the scene written for this case")
    digest = scene_sha256(scene)
    out = Path(output_dir) if output_dir else root / "previews" / digest[:16]
    out.mkdir(parents=True, exist_ok=True)
    # Preview only: the compiler requires VALIDATED, ingest still decides the real state.
    previewable = dataclasses.replace(checked, state="VALIDATED")
    pptx = out / "preview.pptx"
    build = SceneSpecCompiler().compile(
        previewable,
        pptx,
        canonical_path=canonical,
        # case_dir=None: never write the case's render_plan.json/manifests
        case_dir=None,
        strict_native=scene.metadata.get("render_strategy") == "strict_native",
    )
    if backend is None:
        from ppt_restore.rendering.renderers import AutoRenderBackend, LibreOfficeBackend, PowerPointBackend

        backend = {
            "libreoffice": LibreOfficeBackend,
            "powerpoint": PowerPointBackend,
            "auto": AutoRenderBackend,
        }[renderer]()
    rendered = backend.render(pptx, out / "render")
    report = {
        "status": "FAILED",
        "scene_sha256": digest,
        "preview_only": True,
        "build_warnings": list(build.warnings),
        "structural_review_reasons": list(structural.get("review_reasons", [])),
    }
    if not rendered.success or not rendered.images:
        report["error"] = rendered.error or "renderer produced no image"
        write_json(out / "preview.json", report)
        return report
    source = Image.open(canonical).convert("RGB")
    render = Image.open(rendered.images[0]).convert("RGB")
    if render.size != source.size:
        render = render.resize(source.size, Image.LANCZOS)
    render.save(out / "render.png")
    _labelled_row([source, render], ["canonical.png (source)", "your scene rendered (%s)" % rendered.backend]).save(
        out / "side_by_side.png"
    )
    _overlay(source, render).save(out / "diff.png")
    cells = grid_regions(scene, source, render)
    _attach_nodes(cells, scene)
    worst = sorted(
        (c for c in cells if c["mean_abs_error"] >= 0.04), key=lambda c: -c["mean_abs_error"]
    )
    missing = sorted(
        (c for c in cells if c["source_ink"] >= 0.02 and c["render_ink"] < 0.6 * c["source_ink"]),
        key=lambda c: c["render_ink"] - c["source_ink"],
    )
    nodes = node_regions(scene, source, render)
    _save_region_crops(source, render, worst, out / "regions")
    report.update(
        {
            "status": "RENDERED",
            "renderer": rendered.backend,
            "images": {
                "side_by_side": str(out / "side_by_side.png"),
                "diff": str(out / "diff.png"),
                "render": str(out / "render.png"),
                "pptx": str(pptx),
            },
            "metrics": {
                "ssim": round(M.calculate_ssim(render, source), 4),
                "ink_iou": round(M.calculate_ink_iou(render, source), 4),
                "edge_f1": round(M.calculate_edge_f1(render, source), 4),
            },
            "worst_regions": worst[:12],
            "missing_detail_regions": missing[:12],
            "worst_nodes": nodes[:20],
            "how_to_use": [
                "Open side_by_side.png and diff.png (red = differs) and every regions/region_*.png crop.",
                "worst_regions: 1/16 x 1/9 grid cells with the largest colour/geometry difference (crops include one cell of context). Compare source_mean/render_mean of the nodes there; fix fills, gradients, plates, bbox and paint order.",
                "missing_detail_regions: the source has text/icon/edge detail the render lacks, usually missing nodes (decorations, icons, ribbons, separators, small labels) or text that wrapped/shrank differently.",
                "Edit scene.proposed.json, then run preview again. Pixels show where, not why: re-read canonical.png before changing content. Never copy pixel colours blindly into text.",
            ],
        }
    )
    write_json(out / "preview.json", report)
    return report
