import json
import tempfile
import unittest
from pathlib import Path

from ppt_restore.pipeline.host_tasks import next_task, record_full_build
from ppt_restore.pipeline.revisions import propose_revision
from ppt_restore.platform.provenance import sha256_file


class HostTaskTests(unittest.TestCase):
    def test_invalid_v2_ready_report_requests_new_review_not_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.png").write_bytes(b"reference")
            (root / "scene.json").write_text(
                '{"schema_version":"2.0"}', encoding="utf-8"
            )
            pptx = root / "build.pptx"
            pptx.write_bytes(b"built")
            digest = sha256_file(pptx)
            (root / "block_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "blocks": [
                            {
                                "id": "b1",
                                "status": "BUILT",
                                "build_sha256": digest,
                                "build_path": str(pptx),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            path = root / "reviews" / "b1" / digest / "review.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "status": "REVIEW_READY",
                        "pptx_sha256": digest,
                        "scene_sha256": sha256_file(root / "scene.json"),
                    }
                ),
                encoding="utf-8",
            )
            task = next_task(root)
            self.assertEqual(task["status"], "REVIEW_REQUIRED")
            self.assertEqual(task["command_argv"][1], "review")
            self.assertFalse(task["user_confirmation_required"])

    def test_missing_build_before_first_review_requests_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.png").write_bytes(b"source")
            (root / "scene.json").write_text("{}", encoding="utf-8")
            (root / "block_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "blocks": [
                            {
                                "id": "b1",
                                "status": "BUILT",
                                "build_path": str(root / "missing.pptx"),
                                "build_sha256": "old",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            task = next_task(root)
            self.assertEqual(task["status"], "BUILD_REQUIRED")
            self.assertEqual(task["command_argv"][1], "build")

    def test_full_build_advances_to_verify_and_stale_artifacts_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.png").write_bytes(b"reference")
            (root / "scene.json").write_text(
                json.dumps(
                    {
                        "blocks": [{"id": "b1", "bbox_norm": [0, 0, 1000, 1000]}],
                        "nodes": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "block_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "blocks": [{"id": "b1", "status": "APPROVED"}],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(next_task(root)["status"], "FULL_BUILD_REQUIRED")
            pptx = root / "final.pptx"
            pptx.write_bytes(b"full slide")
            record_full_build(root, pptx)
            task = next_task(root)
            self.assertEqual(
                task["command_argv"],
                ["pptrestore", "verify", str(root.resolve()), str(pptx.resolve())],
            )
            report = {
                "gate": {"status": "PREVERIFIED"},
                "provenance": {
                    "pptx_sha256": sha256_file(pptx),
                    "scene_sha256": sha256_file(root / "scene.json"),
                    "input_sha256": sha256_file(root / "canonical.png"),
                },
            }
            (root / "reports" / "verification.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            task = next_task(root)
            self.assertEqual(task["status"], "FINAL_USER_REVIEW_REQUIRED")
            self.assertEqual(task["verification_status"], "PREVERIFIED")
            self.assertIsNone(task["command_argv"])
            report["gate"]["status"] = "NEEDS_REVIEW"
            (root / "reports" / "verification.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            self.assertEqual(next_task(root)["status"], "FINAL_REPAIR_REQUIRED")
            pptx.write_bytes(b"modified")
            self.assertEqual(next_task(root)["status"], "FULL_BUILD_REQUIRED")

    def test_review_routes_content_and_renderer_failures_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.png").write_bytes(b"source")
            (root / "scene.json").write_text("{}", encoding="utf-8")
            pptx = root / "build.pptx"
            pptx.write_bytes(b"built")
            digest = sha256_file(pptx)
            (root / "block_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "blocks": [
                            {
                                "id": "b1",
                                "status": "BUILT",
                                "build_path": str(pptx),
                                "build_sha256": digest,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report_path = root / "reviews" / "b1" / digest / "review.json"
            report_path.parent.mkdir(parents=True)
            for status, expected in [
                ("CONTENT_OR_NATIVE_REPAIR_REQUIRED", "CONTENT_REPAIR_REQUIRED"),
                ("RENDER_FAILED", "RENDER_REPAIR_REQUIRED"),
                ("REVIEW_READY", "AWAITING_VISUAL_REVIEW"),
            ]:
                report_path.write_text(
                    json.dumps(
                        {
                            "status": status,
                            "scene_sha256": sha256_file(root / "scene.json"),
                            "pptx_sha256": digest,
                        }
                    ),
                    encoding="utf-8",
                )
                task = next_task(root)
                self.assertEqual(task["status"], expected)
                self.assertFalse(task["automatic_approval"])
            pptx.write_bytes(b"changed")
            task = next_task(root)
            self.assertEqual(task["status"], "BUILD_REQUIRED")
            self.assertEqual(task["command_argv"][-2:], ["--blocks", "b1"])
            self.assertIn("hybrid_editable", task["command_argv"])
            scene_path = root / "scene.json"
            scene = json.loads(scene_path.read_text(encoding="utf-8"))
            scene.setdefault("metadata", {})["render_strategy"] = "strict_native"
            scene_path.write_text(json.dumps(scene), encoding="utf-8")
            strict_task = next_task(root)
            self.assertIn("strict_native", strict_task["command_argv"])
            self.assertEqual(
                task["after_action"], ["pptrestore", "next", str(root.resolve())]
            )

    def test_missing_source_requests_prepare(self):
        with tempfile.TemporaryDirectory() as directory:
            task = next_task(directory)
            self.assertEqual(task["action"], "prepare")
            self.assertFalse(task["automatic_approval"])

    def test_stale_revision_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scene.json").write_text("{}", encoding="utf-8")
            patch = root / "patch.json"
            patch.write_text('{"base_scene_sha256":"stale"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                propose_revision(root, patch, root / "proposal.json")
            self.assertFalse((root / "proposal.json").exists())
