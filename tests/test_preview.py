"""pptrestore preview: render a proposal next to canonical.png without touching case state."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.cli import main
from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.preview import preview_scene
from ppt_restore.rendering.renderers import RenderResult


class PlainRenderer:
    """Pretend renderer: a white slide, i.e. the dark plate is 'missing'."""

    name = "libreoffice"

    def render(self, pptx, output):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        image = output / "slide-1.png"
        Image.new("RGB", (2880, 1620), "white").save(image)
        return RenderResult(self.name, True, images=[str(image)], pptx_sha256=sha256_file(pptx))


class PreviewTests(unittest.TestCase):
    def test_preview_reports_regions_and_leaves_case_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            image = Image.new("RGB", (1440, 810), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle([900, 450, 1300, 750], fill=(20, 60, 140))
            for y in range(100, 200, 12):
                draw.line([100, y, 600, y], fill="black", width=3)
            image.save(source)
            case = root / "case"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["prepare", str(source), "--case-dir", str(case), "--ocr", "none"]), 0)
            request = json.loads((case / "agent_request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["self_check_contract"]["command"][1], "preview")
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                (
                    SceneNode("title", "text", "title", (100, 100, 500, 100), block_id="a",
                              payload={"text": "Hello"}),
                ),
                blocks=({"id": "a", "name": "All", "bbox_norm": [0, 0, 1000, 1000]},),
            )
            proposal = case / "scene.proposed.json"
            proposal.write_text(scene.to_json(), encoding="utf-8")
            before = sorted(p.name for p in case.iterdir())
            report = preview_scene(case, proposal, backend=PlainRenderer())
            self.assertEqual(report["status"], "RENDERED")
            for key in ("side_by_side", "diff", "render", "pptx"):
                self.assertTrue(Path(report["images"][key]).is_file(), key)
            with Image.open(report["images"]["render"]) as rendered:
                self.assertEqual(rendered.size, (1440, 810))
            worst = report["worst_regions"][0]
            # the dark plate (x 625..903, y 556..926 in 0-1000) dominates the error
            self.assertGreaterEqual(worst["bbox_norm"][0], 562)
            self.assertGreaterEqual(worst["bbox_norm"][1], 444)
            self.assertTrue(Path(worst["crop"]).is_file())
            self.assertTrue(report["missing_detail_regions"])
            self.assertIn("title", report["worst_nodes"][0]["node_id"])
            self.assertTrue(report["preview_only"])
            # previews/ is the only new entry; scene.json and gates are never written
            after = sorted(p.name for p in case.iterdir())
            self.assertEqual(sorted(set(after) - set(before)), ["previews"])

    def test_text_size_hint_measures_glyph_height(self):
        from ppt_restore.quality.preview import text_size_hints

        def slide(band):
            image = Image.new("RGB", (1440, 810), "white")
            draw = ImageDraw.Draw(image)
            for x in range(110, 500, 14):  # glyph-like strokes of one text line
                draw.rectangle([x, 120, x + 6, 120 + band], fill="black")
            return image

        node = SceneNode("body", "text", "body", (100, 110, 420, 40),
                         payload={"text": "x"}, style={"font_size_pt": 12})
        scene = SceneSpecV2("2.0", "a" * 64, "b" * 64, {"width_px": 1440, "height_px": 810}, (node,))
        hints = text_size_hints(scene, slide(16), slide(12))
        self.assertEqual(hints[0]["node_id"], "body")
        self.assertAlmostEqual(hints[0]["glyph_height_ratio"], 17 / 13.0, places=3)
        self.assertEqual(hints[0]["suggested_font_size_pt"], 15.5)
        self.assertIn("glyphs smaller than source", hints[0]["problems"])
        self.assertEqual(text_size_hints(scene, slide(12), slide(12)), [])

    def test_cli_is_registered(self):
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit):
            main(["preview", "--help"])
        self.assertIn("scene", out.getvalue())


if __name__ == "__main__":
    unittest.main()
