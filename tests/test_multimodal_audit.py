import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ppt_restore.cli import main
from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.pipeline.block_gate import init_block_gate
from ppt_restore.pipeline.workflow import ingest_scene, prepare_case
from ppt_restore.platform.doctor import doctor
from ppt_restore.platform.evidence import extract_evidence
from ppt_restore.platform.ocr import ImportedTextProvider, TextDetection
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.audit import make_content_audit, validate_content_audit


class MultimodalAuditTests(unittest.TestCase):
    def _scene_case(self, root):
        source = root / "source.png"
        Image.new("RGB", (1440, 810), "white").save(source)
        prepare_case(source, root / "case", ocr_mode="none")
        case = root / "case"
        extract_evidence(
            case / "canonical.png",
            ocr_provider=ImportedTextProvider(
                [TextDetection("Hello", (10, 10, 100, 30), 0.99, "imported")]
            ),
            output_path=case / "evidence.json",
        )
        scene = SceneSpecV2(
            "2.0",
            sha256_file(case / "canonical.png"),
            sha256_file(case / "evidence.json"),
            {"width_px": 1440, "height_px": 810},
            (
                SceneNode(
                    "title",
                    "text",
                    "title",
                    (10, 10, 100, 30),
                    block_id="header",
                    evidence_refs=("ocr-0001",),
                    payload={"text": "Hello"},
                ),
            ),
            blocks=({"id": "header", "bbox_norm": [0, 0, 1000, 1000]},),
        )
        proposed = case / "scene.proposed.json"
        proposed.write_text(scene.to_json() + "\n", encoding="utf-8")
        audit = make_content_audit(scene, confirmed=True)
        audit_path = case / "content_audit.proposed.json"
        audit_path.write_text(audit.to_json() + "\n", encoding="utf-8")
        return case, proposed, audit_path, scene

    def test_two_pass_conflict_is_review(self):
        with tempfile.TemporaryDirectory() as directory:
            case, proposed, audit_path, _ = self._scene_case(Path(directory))
            data = json.loads(audit_path.read_text(encoding="utf-8"))
            data["passes"]["pass_2_content_audit"]["status"] = "conflict"
            audit_path.write_text(json.dumps(data), encoding="utf-8")
            result = ingest_scene(case, proposed, content_audit_path=audit_path)
            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertIn(
                "pass_2_content_audit is not complete",
                result["audit"]["review_reasons"],
            )
            self.assertFalse((case / "scene.json").exists())

    def test_audit_template_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            case, proposed, _, scene = self._scene_case(Path(directory))
            template = make_content_audit(scene)
            self.assertEqual(template.status, "NEEDS_REVIEW")
            self.assertEqual(
                template.passes["pass_2_content_audit"]["status"], "awaiting"
            )
            self.assertTrue(
                all(item["status"] == "NEEDS_REVIEW" for item in template.items)
            )

    def test_uncalibrated_perfect_confidence_is_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "canonical.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            evidence = extract_evidence(
                source, ocr_mode="none", output_path=root / "evidence.json"
            )
            nodes = tuple(
                SceneNode(
                    "text-%d" % index,
                    "text",
                    "body",
                    (10, 10 + index * 35, 200, 30),
                    confidence=1.0,
                    evidence_refs=("region-header",),
                    payload={"text": "Text %d" % index},
                )
                for index in range(5)
            )
            scene = SceneSpecV2(
                "2.0",
                sha256_file(source),
                sha256_file(root / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                nodes,
            )
            audit = make_content_audit(scene, confirmed=True)
            report = validate_content_audit(audit, scene, evidence)
            self.assertFalse(report["valid"])
            self.assertTrue(
                any(
                    "suspicious perfect" in reason
                    for reason in report["review_reasons"]
                )
            )

    def test_audited_inventory_builds_and_reconciles_to_dom(self):
        with tempfile.TemporaryDirectory() as directory:
            case, proposed, audit_path, _ = self._scene_case(Path(directory))
            result = ingest_scene(case, proposed, content_audit_path=audit_path)
            self.assertEqual(result["status"], "VALIDATED")
            inventory = json.loads(
                (case / "content_inventory.json").read_text(encoding="utf-8")
            )
            self.assertTrue(inventory["not_source_recognition_proof"])
            self.assertEqual(inventory["audit_status"], "VALIDATED")
            output = Path(directory) / "result.pptx"
            init_block_gate(case, proposed)
            self.assertEqual(
                main(
                    ["build", str(case), "--blocks", "header", "--output", str(output)]
                ),
                0,
            )
            check = json.loads(
                (case / "reports" / "content_dom_check.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(check["valid"])
            self.assertEqual(check["missing_critical"], [])

    def test_critical_inventory_omission_fails_build(self):
        with tempfile.TemporaryDirectory() as directory:
            case, proposed, audit_path, _ = self._scene_case(Path(directory))
            self.assertEqual(
                ingest_scene(case, proposed, content_audit_path=audit_path)["status"],
                "VALIDATED",
            )
            inventory_path = case / "content_inventory.json"
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
            data["items"][0]["content"]["text"] = "Omitted"
            inventory_path.write_text(json.dumps(data), encoding="utf-8")
            output = Path(directory) / "result.pptx"
            init_block_gate(case, proposed)
            self.assertEqual(
                main(
                    ["build", str(case), "--blocks", "header", "--output", str(output)]
                ),
                1,
            )
            check = json.loads(
                (case / "reports" / "content_dom_check.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(check["status"], "NEEDS_REVIEW")
            self.assertEqual(check["missing_critical"][0]["node_id"], "title")

    def test_optional_capability_statuses_do_not_block_core(self):
        report = doctor()
        capabilities = report.capabilities
        self.assertTrue(report.ok)
        self.assertEqual(capabilities["core"], "available")
        self.assertIn(
            capabilities["font_strict_validation"].split(":", 1)[0],
            ("available", "degraded"),
        )
        self.assertIn(
            capabilities["ocr_crosscheck"].split(":", 1)[0],
            ("available", "degraded", "discovered_unverified"),
        )
        self.assertIn(
            capabilities["formal_powerpoint_acceptance"].split(":", 1)[0],
            ("available", "blocked"),
        )


if __name__ == "__main__":
    unittest.main()
