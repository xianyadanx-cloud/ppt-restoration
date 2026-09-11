import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ppt_restore.platform.provenance import sha256_file
from ppt_restore.quality.render_probe import run_render_probe
from ppt_restore.rendering.renderers import RenderResult


class ProbeTests(unittest.TestCase):
    def test_blank_successful_export_does_not_unlock_optimization(self):
        class BlankBackend:
            def render(self, pptx, output):
                output.mkdir(parents=True)
                image = output / "slide.png"
                Image.new("RGB", (1000, 600), "white").save(image)
                return RenderResult(
                    "libreoffice",
                    True,
                    images=[str(image)],
                    pptx_sha256=sha256_file(pptx),
                )

        with tempfile.TemporaryDirectory() as directory:
            report = run_render_probe(BlankBackend(), directory)
            self.assertFalse(report["automatic_optimization_allowed"])
            self.assertTrue(report["checks"]["real_render"])
            self.assertFalse(report["checks"]["gradient_direction"])
            self.assertFalse(report["checks"]["text_visible"])
            self.assertTrue(Path(report["report_path"]).is_file())
