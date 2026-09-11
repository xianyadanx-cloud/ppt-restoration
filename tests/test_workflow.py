import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.pipeline.workflow import ingest_scene, prepare_case
from ppt_restore.platform.evidence import extract_evidence
from ppt_restore.platform.ocr import ImportedTextProvider, TextDetection
from ppt_restore.platform.provenance import sha256_file


class WorkflowTests(unittest.TestCase):
    def test_prepare_and_ingest_valid_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            image = Image.new("RGB", (1440, 810), "white")
            ImageDraw.Draw(image).rectangle((20, 20, 500, 90), fill="#DCEBFF")
            image.save(source)
            result = prepare_case(source, root / "case", ocr_mode="none")
            case = root / "case"
            # Replace the evidence with deterministic imported text to avoid
            # depending on whether Vision/Tesseract exists on the test host.
            extract_evidence(
                case / "canonical.png",
                ocr_provider=ImportedTextProvider(
                    [TextDetection("标题", (20, 20, 150, 40), 0.99, "imported")]
                ),
                output_path=case / "evidence.json",
            )
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810, "color_space": "sRGB", "dpi": 96},
                (
                    SceneNode(
                        "title",
                        "text",
                        "title",
                        (20, 20, 150, 40),
                        confidence=0.99,
                        evidence_refs=("ocr-0001",),
                        payload={"text": "标题"},
                    ),
                ),
            )
            proposed = case / "scene.proposed.json"
            proposed.write_text(scene.to_json(indent=2) + "\n", encoding="utf-8")
            ingested = ingest_scene(case, proposed, allow_missing_audit=True)
            self.assertEqual(ingested["status"], "VALIDATED")
            self.assertEqual(ingested["audit"]["status"], "MISSING_COMPATIBILITY")
            self.assertTrue(ingested["audit"]["warning"])
            self.assertTrue((case / "scene.json").is_file())
            self.assertEqual(result["case_dir"], str(case))

    def test_text_conflict_is_review_without_overwriting_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            prepare_case(source, root / "case", ocr_mode="none")
            case = root / "case"
            extract_evidence(
                case / "canonical.png",
                ocr_provider=ImportedTextProvider(
                    [TextDetection("正确", (10, 10, 100, 30), 0.99, "imported")]
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
                        evidence_refs=("ocr-0001",),
                        payload={"text": "错误"},
                    ),
                ),
            )
            proposed = case / "scene.proposed.json"
            proposed.write_text(scene.to_json(), encoding="utf-8")
            ingested = ingest_scene(case, proposed, allow_missing_audit=True)
            self.assertEqual(ingested["status"], "NEEDS_REVIEW")
            self.assertFalse((case / "scene.json").exists())

    def test_uncovered_high_confidence_ocr_is_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            prepare_case(source, root / "case", ocr_mode="none")
            case = root / "case"
            extract_evidence(
                case / "canonical.png",
                ocr_provider=ImportedTextProvider(
                    [TextDetection("漏掉的标题", (10, 10, 120, 30), 0.99, "imported")]
                ),
                output_path=case / "evidence.json",
            )
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                (),
            )
            proposed = case / "scene.proposed.json"
            proposed.write_text(scene.to_json(), encoding="utf-8")
            ingested = ingest_scene(case, proposed, allow_missing_audit=True)
            self.assertEqual(ingested["status"], "NEEDS_REVIEW")

    def test_agent_request_explicitly_marks_disabled_ocr_degradation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            result = prepare_case(source, root / "case", ocr_mode="none")
            request = json.loads(
                (root / "case" / "agent_request.json").read_text(encoding="utf-8")
            )
            self.assertEqual(request["ocr"]["status"], "disabled")
            self.assertTrue(request["degradation"]["active"])
            self.assertTrue(request["degradation"]["critical_text_review_required"])
            self.assertTrue(
                request["degradation"]["do_not_infer_text_absence_from_empty_ocr"]
            )
            self.assertEqual(result["degradation"], request["degradation"])
            self.assertTrue(request["canonical_path"].endswith("/canonical.png"))
            self.assertEqual(len(request["canonical_sha256"]), 64)
            self.assertEqual(len(request["evidence_sha256"]), 64)

    def test_missing_audit_is_review_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            prepare_case(source, root / "case", ocr_mode="none")
            case = root / "case"
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                (),
            )
            proposed = case / "scene.proposed.json"
            proposed.write_text(scene.to_json(), encoding="utf-8")
            result = ingest_scene(case, proposed)
            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertIn(
                "pass_2_content_audit is required for v2 ingest",
                result["audit"]["review_reasons"],
            )
            self.assertFalse((case / "scene.json").exists())


if __name__ == "__main__":
    unittest.main()
