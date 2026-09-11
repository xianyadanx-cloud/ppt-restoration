"""Synthetic workflow regression. Mock pixels and approvals are not visual acceptance."""

import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from ppt_restore.cli import main
from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.pipeline.host_tasks import next_task
from ppt_restore.platform.evidence import extract_evidence
from ppt_restore.platform.ocr import ImportedTextProvider, TextDetection
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.audit import make_content_audit
from ppt_restore.rendering.renderers import RenderResult


class SyntheticRenderer:
    """Return blank pixels for a blank synthetic reference, with real PPT hashes."""

    name = "libreoffice"

    def render(self, pptx, output):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        image = output / "synthetic.png"
        Image.new("RGB", (1440, 810), "white").save(image)
        return RenderResult(
            self.name,
            True,
            images=[str(image)],
            pptx_sha256=sha256_file(pptx),
            acceptance_eligible=False,
            renderer_version="synthetic-test-only",
        )


class EndToEndTests(unittest.TestCase):
    def test_two_blocks_to_full_build_and_preverification(self):
        self._exercise(False)

    def test_hybrid_decoration_survives_block_review(self):
        self._exercise(True)

    def _exercise(self, hybrid):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "case"
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)

            def run(*args):
                stream = io.StringIO()
                with (
                    contextlib.redirect_stdout(stream),
                    contextlib.redirect_stderr(stream),
                ):
                    result = main([str(a) for a in args])
                self.assertEqual(result, 0, stream.getvalue())
                return json.loads(stream.getvalue())

            run("prepare", source, "--case-dir", case, "--ocr", "none")
            extract_evidence(
                case / "canonical.png",
                output_path=case / "evidence.json",
                ocr_provider=ImportedTextProvider(
                    [
                        TextDetection("First", (20, 20, 200, 40), 0.99, "test"),
                        TextDetection("Second", (20, 450, 200, 40), 0.99, "test"),
                    ]
                ),
            )
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                (
                    SceneNode(
                        "first",
                        "text",
                        "title",
                        (20, 20, 200, 40),
                        block_id="a",
                        evidence_refs=("ocr-0001",),
                        payload={"text": "First"},
                    ),
                    SceneNode(
                        "second",
                        "text",
                        "body",
                        (20, 450, 200, 40),
                        block_id="b",
                        evidence_refs=("ocr-0002",),
                        payload={"text": "Second"},
                    ),
                ),
                blocks=(
                    {"id": "a", "name": "Top", "bbox_norm": [0, 0, 1000, 500]},
                    {"id": "b", "name": "Bottom", "bbox_norm": [0, 500, 1000, 500]},
                ),
            )
            if hybrid:
                scene = replace(
                    scene,
                    nodes=scene.nodes
                    + (
                        SceneNode(
                            "decoration",
                            "image",
                            "decoration",
                            (900, 100, 100, 100),
                            block_id="a",
                            render_strategy="raster",
                            payload={"source_bbox_norm": [625, 124, 70, 124]},
                        ),
                    ),
                )
            proposal, audit = case / "proposal.json", case / "audit.json"
            proposal.write_text(scene.to_json(), encoding="utf-8")
            audit.write_text(
                make_content_audit(scene, confirmed=True).to_json(), encoding="utf-8"
            )
            run("ingest", case, proposal, "--content-audit", audit)
            blueprint = run("blueprint", case)
            self.assertTrue(Path(blueprint["block_map"]).is_file())
            run("block-init", case, blueprint["blueprint"])
            for block in ("a", "b"):
                task = next_task(case)
                run(*task["command_argv"][1:])
                with patch(
                    "ppt_restore.cli.commands.review._backend",
                    return_value=SyntheticRenderer(),
                ):
                    report = run("review", case, "--block", block)
                self.assertEqual(report["status"], "REVIEW_READY")
                report_path = (
                    case / "reviews" / block / report["pptx_sha256"] / "review.json"
                )
                # Explicit simulated approvals apply only to this temporary test case.
                run(
                    "block-approve",
                    case,
                    block,
                    "--review-report",
                    report_path,
                    "--user-confirmed",
                )
            output = root / "final.pptx"
            result = run("build", case, "--output", output)
            self.assertEqual(result["picture_count"], int(hybrid))
            with patch(
                "ppt_restore.cli.services._backend", return_value=SyntheticRenderer()
            ):
                report = run("verify", case, output)
            self.assertEqual(report["gate"]["status"], "PREVERIFIED")
            self.assertTrue(report["content_dom_check"]["valid"])
            self.assertTrue(report["build_manifest"]["valid"])
