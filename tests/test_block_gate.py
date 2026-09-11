import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from ppt_restore.pipeline.block_gate import (
    active_block,
    approve_block,
    assert_build_allowed,
    init_block_gate,
    read_block_gate,
    record_block_build,
)


class BlockGateTests(unittest.TestCase):
    def test_v2_approval_requires_ready_real_render_and_intact_evidence(self):
        from ppt_restore.platform.provenance import sha256_file

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_scene(root)
            scene_path = root / "scene.json"
            scene = json.loads(scene_path.read_text(encoding="utf-8"))
            scene["schema_version"] = "2.0"
            scene_path.write_text(json.dumps(scene), encoding="utf-8")
            init_block_gate(root, scene_path)
            pptx = root / "step.pptx"
            pptx.write_bytes(b"synthetic fixture")
            record_block_build(root, ["b1"], pptx)
            report_path = root / "review.json"
            report = {"pptx_sha256": sha256_file(pptx)}
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REVIEW_READY"):
                approve_block(root, "b1", report_path, user_confirmed=True)
            evidence = root / "evidence.png"
            evidence.write_bytes(b"synthetic evidence")
            report.update(
                status="REVIEW_READY",
                block_id="b1",
                scene_sha256=sha256_file(scene_path),
                render={
                    "success": True,
                    "backend": "fast_preview",
                    "pptx_sha256": sha256_file(pptx),
                },
                evidence={
                    key: str(evidence)
                    for key in ("reference", "rendered", "difference", "cumulative")
                },
                evidence_sha256={
                    key: sha256_file(evidence)
                    for key in ("reference", "rendered", "difference", "cumulative")
                },
            )
            report_path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "real-render"):
                approve_block(root, "b1", report_path, user_confirmed=True)
            report["render"]["backend"] = "libreoffice"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            evidence.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "evidence missing or changed"):
                approve_block(root, "b1", report_path, user_confirmed=True)
            evidence.write_bytes(b"synthetic evidence")
            pptx.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "PPTX is missing or changed"):
                approve_block(root, "b1", report_path, user_confirmed=True)
            pptx.write_bytes(b"synthetic fixture")
            self.assertEqual(
                active_block(
                    approve_block(root, "b1", report_path, user_confirmed=True)
                ),
                "b2",
            )

    def test_source_and_canvas_changes_invalidate_build_binding(self):
        from ppt_restore.pipeline.block_gate import _scene_block_state

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_scene(root)
            (root / "canonical.png").write_bytes(b"source")
            baseline = _scene_block_state(root)["blocks"]["b1"]["semantic_sha256"]
            (root / "canonical.png").write_bytes(b"changed reference")
            changed = _scene_block_state(root)["blocks"]["b1"]["semantic_sha256"]
            self.assertNotEqual(baseline, changed)
            scene = json.loads((root / "scene.json").read_text(encoding="utf-8"))
            scene["canvas"] = {"width_px": 1000, "height_px": 1000}
            (root / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
            self.assertNotEqual(
                changed, _scene_block_state(root)["blocks"]["b1"]["semantic_sha256"]
            )

    def test_missing_gate_cannot_bypass_block_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_scene(root)
            for selected in (None, ["b1"], ["b2"]):
                with self.assertRaisesRegex(ValueError, "blueprint approval required"):
                    assert_build_allowed(root, selected)
            scene = json.loads((root / "scene.json").read_text(encoding="utf-8"))
            scene.pop("blocks")
            (root / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "blueprint approval required"):
                assert_build_allowed(root, None)

    def test_review_rejects_changed_scene_before_rendering(self):
        from ppt_restore.quality.review import review_block

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_scene(root)
            blueprint = root / "blueprint.json"
            blueprint.write_text(
                json.dumps(
                    {
                        "blocks": json.loads(
                            (root / "scene.json").read_text(encoding="utf-8")
                        )["blocks"]
                    }
                ),
                encoding="utf-8",
            )
            init_block_gate(root, blueprint)
            pptx = root / "step.pptx"
            pptx.write_bytes(b"original")
            record_block_build(root, ["b1"], pptx)
            scene = json.loads((root / "scene.json").read_text(encoding="utf-8"))
            scene["nodes"][0]["payload"]["text"] = "Changed title"
            (root / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
            (root / "canonical.png").write_bytes(b"reference")
            from ppt_restore.pipeline.host_tasks import next_task

            self.assertEqual(next_task(root)["status"], "BUILD_REQUIRED")
            backend = Mock()
            with self.assertRaisesRegex(ValueError, "scene changed"):
                review_block(root, "b1", backend)
            backend.render.assert_not_called()

    @staticmethod
    def _write_scene(root, body_text="Body"):
        (root / "scene.json").write_text(
            json.dumps(
                {
                    "blocks": [
                        {"id": "b1", "name": "Header", "bbox_norm": [0, 0, 1000, 100]},
                        {"id": "b2", "name": "Body", "bbox_norm": [0, 100, 1000, 900]},
                    ],
                    "nodes": [
                        {"id": "title", "block_id": "b1", "payload": {"text": "Title"}},
                        {
                            "id": "body",
                            "block_id": "b2",
                            "payload": {"text": body_text},
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_sequential_fail_closed_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blueprint = root / "blueprint.json"
            blueprint.write_text(
                json.dumps(
                    {
                        "blocks": [
                            {
                                "id": "b1",
                                "name": "Header",
                                "bbox_norm": [0, 0, 1000, 100],
                            },
                            {
                                "id": "b2",
                                "name": "Body",
                                "bbox_norm": [0, 100, 1000, 900],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self._write_scene(root)
            gate = init_block_gate(root, blueprint)
            self.assertEqual(active_block(gate), "b1")
            with self.assertRaises(ValueError):
                assert_build_allowed(root, None)
            with self.assertRaises(ValueError):
                assert_build_allowed(root, ["b2"])
            self.assertIsNotNone(assert_build_allowed(root, ["b1"]))

            pptx = root / "step.pptx"
            pptx.write_bytes(b"pptx")
            record_block_build(root, ["b1"], pptx)
            built = read_block_gate(root)["blocks"][0]
            self.assertEqual(built["status"], "BUILT")
            report = root / "review.json"
            report.write_text(
                json.dumps(
                    {"status": "REVIEWED", "pptx_sha256": built["build_sha256"]}
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                approve_block(root, "b1", report, user_confirmed=False)
            gate = approve_block(root, "b1", report, user_confirmed=True)
            self.assertEqual(active_block(gate), "b2")
            self.assertIsNotNone(assert_build_allowed(root, ["b1", "b2"]))
            with self.assertRaises(ValueError):
                assert_build_allowed(root, None)

            self._write_scene(root, body_text="Body changed")
            self.assertIsNotNone(assert_build_allowed(root, ["b1", "b2"]))
            scene = json.loads((root / "scene.json").read_text(encoding="utf-8"))
            scene["nodes"][0]["payload"]["text"] = "Changed approved title"
            (root / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved Block b1 changed"):
                assert_build_allowed(root, ["b1", "b2"])

    def test_approval_rejects_stale_or_unbound_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blueprint = root / "blueprint.json"
            blueprint.write_text(
                json.dumps(
                    {
                        "blocks": [
                            {"id": "b1", "bbox_norm": [0, 0, 1000, 1000]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            init_block_gate(root, blueprint)
            pptx = root / "step.pptx"
            pptx.write_bytes(b"latest build")
            record_block_build(root, ["b1"], pptx)

            report = root / "review.json"
            report.write_text('{"status":"REVIEWED"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pptx_sha256"):
                approve_block(root, "b1", report, user_confirmed=True)

            report.write_text(json.dumps({"pptx_sha256": "0" * 64}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "latest Block build"):
                approve_block(root, "b1", report, user_confirmed=True)


if __name__ == "__main__":
    unittest.main()
