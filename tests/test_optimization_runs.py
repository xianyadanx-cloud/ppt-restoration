import json
import tempfile
import unittest
from pathlib import Path

from ppt_restore.pipeline.host_tasks import next_task
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.optimization_runs import new_run, save_result


class OptimizationRunTests(unittest.TestCase):
    def test_next_recovers_only_current_intact_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canonical.png").write_bytes(b"source")
            (root / "scene.json").write_text("{}", encoding="utf-8")
            (root / "block_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "blocks": [{"id": "b1", "status": "PENDING"}],
                    }
                ),
                encoding="utf-8",
            )
            run = new_run(root)
            save_result(
                run,
                root,
                {"nodes": []},
                {"improved": True, "block_id": "b1"},
                sha256_file(root / "scene.json"),
            )
            task = next_task(root)
            self.assertEqual(task["status"], "CANDIDATE_AUDIT_REQUIRED")
            self.assertIsNone(task["command_argv"])
            self.assertEqual(task["after_audit_argv"][1], "ingest")
            (root / "canonical.png").write_bytes(b"different source")
            self.assertEqual(next_task(root)["status"], "BUILD_REQUIRED")
            (root / "canonical.png").write_bytes(b"source")
            (run / "best_scene.json").write_text("{}", encoding="utf-8")
            self.assertEqual(next_task(root)["status"], "BUILD_REQUIRED")
            (root / "scene.json").write_text('{"new": true}', encoding="utf-8")
            self.assertEqual(next_task(root)["status"], "BUILD_REQUIRED")

    def test_runs_preserve_history_and_require_fresh_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = new_run(root), new_run(root)
            self.assertNotEqual(first, second)
            old = save_result(
                first, root, {"nodes": []}, {"improved": True}, "base-one"
            )
            new = save_result(
                second, root, {"nodes": []}, {"improved": False}, "base-two"
            )
            self.assertEqual(
                json.loads((first / "optimization.json").read_text(encoding="utf-8")),
                old,
            )
            self.assertEqual(old["next_action"], "AUDIT_AND_INGEST_REQUIRED")
            self.assertIn(
                str(first / "content_audit.proposed.json"), old["after_audit_argv"]
            )
            self.assertFalse((first / "content_audit.proposed.json").exists())
            self.assertEqual(new["next_action"], "INSPECT_NO_IMPROVEMENT")
            self.assertIsNone(new["after_audit_argv"])
            self.assertFalse(new["automatic_approval"])
