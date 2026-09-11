import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from ppt_restore.quality.gates import (
    GateEngine,
    QualityGateConfig,
    QualityStatus,
    inspect_picture_count,
)
from ppt_restore.quality.metrics import MetricEngine
from ppt_restore.rendering.renderers import RenderResult

SLIDE_XML = "<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'><p:cSld/></p:sld>"
PIC_SLIDE_XML = "<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'><p:cSld><p:pic/></p:cSld></p:sld>"


def write_pptx(path, xml=SLIDE_XML):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", xml)


class GateTests(unittest.TestCase):
    def test_missing_input_cannot_pass(self):
        result = GateEngine().evaluate(
            input_path="missing.png", render_result=RenderResult("powerpoint", True)
        )
        self.assertEqual(result.status, QualityStatus.INVALID_INPUT)
        self.assertFalse(result.passed)

    def test_picture_count_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            pptx = Path(temp) / "slide.pptx"
            write_pptx(pptx, PIC_SLIDE_XML)
            self.assertEqual(inspect_picture_count(pptx)["picture_count"], 1)
            image = Image.new("RGB", (20, 20), "white")
            report = MetricEngine().evaluate(None, image, image)
            result = GateEngine().evaluate(
                metric_report=report,
                render_result=RenderResult(
                    "powerpoint", True, acceptance_eligible=True
                ),
                pptx_path=pptx,
            )
        self.assertEqual(result.status, QualityStatus.FAIL)
        self.assertFalse(result.passed)

    def test_hybrid_gate_allows_picture_when_configured(self):
        with tempfile.TemporaryDirectory() as temp:
            pptx = Path(temp) / "slide.pptx"
            write_pptx(pptx, PIC_SLIDE_XML)
            image = Image.new("RGB", (20, 20), "white")
            report = MetricEngine().evaluate(None, image, image)
            result = GateEngine(QualityGateConfig(strict_native=False)).evaluate(
                metric_report=report,
                render_result=RenderResult("libreoffice", True),
                pptx_path=pptx,
            )
        self.assertEqual(result.status, QualityStatus.PREVERIFIED)

    def test_libreoffice_can_only_preverify(self):
        image = Image.new("RGB", (20, 20), "white")
        report = MetricEngine().evaluate(None, image, image)
        result = GateEngine().evaluate(
            metric_report=report, render_result=RenderResult("libreoffice", True)
        )
        self.assertEqual(result.status, QualityStatus.PREVERIFIED)
        self.assertFalse(result.passed)

    def test_wps_can_only_preverify(self):
        image = Image.new("RGB", (20, 20), "white")
        report = MetricEngine().evaluate(None, image, image)
        result = GateEngine().evaluate(
            metric_report=report,
            render_result=RenderResult(
                "wps", True, metadata={"wps_mode": "imported_pdf", "imported_pdf": True}
            ),
        )
        self.assertEqual(result.status, QualityStatus.PREVERIFIED)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
