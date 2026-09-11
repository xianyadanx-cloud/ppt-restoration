"""Measured node-region evidence; never infer recognition errors from pixels."""

import hashlib

from PIL import ImageChops, ImageStat


def localize_issues(scene, block_id, source, actual, output_dir, scene_hash, pptx_hash):
    issues = []
    width, height = float(scene.canvas["width_px"]), float(scene.canvas["height_px"])
    for node in scene.nodes:
        if node.block_id != block_id:
            continue
        x, y, w, h = node.bbox_px
        common = {
            "block_id": block_id,
            "node_id": node.id,
            "scene_sha256": scene_hash,
            "pptx_sha256": pptx_hash,
            "detection_source": "program_measurement",
            "confidence": None,
            "allowed_fields": ["bbox_px", "style"],
            "bbox_norm": [
                x * 1000 / width,
                y * 1000 / height,
                w * 1000 / width,
                h * 1000 / height,
            ],
        }
        if x < 0 or y < 0 or x + w > width or y + h > height:
            issues.append(
                dict(
                    common,
                    category="OUTSIDE_CANVAS",
                    priority=1,
                    evidence={"scene_node": node.to_dict()},
                    confidence=1.0,
                )
            )
        box = (
            max(0, round(x * source.width / width)),
            max(0, round(y * source.height / height)),
            min(source.width, round((x + w) * source.width / width)),
            min(source.height, round((y + h) * source.height / height)),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        ref, got = source.crop(box), actual.crop(box)
        difference = ImageChops.difference(ref, got)
        error = sum(ImageStat.Stat(difference).mean) / (3 * 255)
        if error < 0.08:
            continue
        # Hash rather than interpolate model-provided node IDs into paths.
        node_dir = (
            output_dir / "nodes" / hashlib.sha256(node.id.encode()).hexdigest()[:16]
        )
        node_dir.mkdir(parents=True, exist_ok=True)
        evidence = {}
        for name, image in (
            ("reference", ref),
            ("rendered", got),
            ("difference", difference),
        ):
            path = node_dir / (name + ".png")
            image.save(path)
            evidence[name] = str(path)
        issues.append(
            dict(
                common,
                category="NODE_REGION_MISMATCH",
                priority=2,
                evidence=evidence,
                measurement={
                    "mean_absolute_rgb_error": error,
                    "source_box_px": list(box),
                },
                interpretation="Region differs; overlap, position, text or style may contribute. Re-read evidence before choosing a fix.",
            )
        )
    return sorted(
        issues,
        key=lambda issue: (
            issue["priority"],
            -issue.get("measurement", {}).get("mean_absolute_rgb_error", 0),
            issue["node_id"],
        ),
    )
