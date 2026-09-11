"""Prepare a reviewable block map from the current semantic proposal."""

import tempfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.platform.io import read_scene_any, write_json
from ppt_restore.platform.provenance import sha256_file


def make_blueprint(case_dir):
    root = Path(case_dir).resolve()
    scene = read_scene_any(root)
    if not isinstance(scene, SceneSpecV2) or not scene.blocks:
        raise ValueError("blueprint requires a v2 scene with explicit blocks")
    canonical = root / "canonical.png"
    if scene.canonical_sha256 != sha256_file(canonical):
        raise ValueError("reference image changed; ingest again before blueprint")
    out = root / "blueprints"
    out.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="review-", dir=str(out)))
    with Image.open(canonical) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    colors = ["#DC2626", "#2563EB", "#059669", "#9333EA", "#EA580C"]
    rows = []
    for index, block in enumerate(scene.blocks, 1):
        l, t, w, h = block["bbox_norm"]
        box = (
            round(l * image.width / 1000),
            round(t * image.height / 1000),
            round((l + w) * image.width / 1000),
            round((t + h) * image.height / 1000),
        )
        color = colors[(index - 1) % len(colors)]
        draw.rectangle(box, outline=color, width=3)
        draw.rectangle((box[0], box[1], box[0] + 44, box[1] + 20), fill=color)
        draw.text((box[0] + 4, box[1] + 3), "B%d" % index, fill="white")
        nodes = [n for n in scene.nodes if n.block_id == block["id"]]
        rows.append(
            {
                "index": index,
                "id": block["id"],
                "name": block.get("name", block["id"]),
                "bbox_norm": list(block["bbox_norm"]),
                "node_count": len(nodes),
                "node_kinds": dict(Counter(n.kind for n in nodes)),
                "font_sizes_pt": sorted(
                    {
                        float(n.style["font_size_pt"])
                        for n in nodes
                        if n.style.get("font_size_pt")
                    }
                ),
                "fills": sorted(
                    {str(n.style["fill"]) for n in nodes if n.style.get("fill")}
                ),
            }
        )
    image.save(run / "block_map.png")
    write_json(run / "blueprint.json", {"blocks": list(scene.blocks)})
    report = {
        "status": "USER_CONFIRMATION_REQUIRED",
        "scene_sha256": sha256_file(root / "scene.json"),
        "canonical_sha256": sha256_file(canonical),
        "blocks": rows,
        "block_map": str(run / "block_map.png"),
        "blueprint": str(run / "blueprint.json"),
        "after_user_confirmation_argv": [
            "pptrestore",
            "block-init",
            str(root),
            str(run / "blueprint.json"),
        ],
    }
    write_json(run / "report.json", report)
    return report
