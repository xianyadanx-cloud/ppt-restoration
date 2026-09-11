import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ppt_restore.rendering.renderers import (
    LibreOfficeBackend,
    PowerPointBackend,
    WpsBackend,
    read_wps_version,
)


class RenderBackendTests(unittest.TestCase):
    def test_macos_font_configuration_is_process_local(self):
        import os

        from ppt_restore.rendering.renderers import isolated_font_environment

        with tempfile.TemporaryDirectory() as directory:
            with (
                patch(
                    "ppt_restore.rendering.renderers.platform.system",
                    return_value="Darwin",
                ),
                patch.dict(os.environ, {}, clear=True),
            ):
                env, metadata = isolated_font_environment(directory)
                self.assertNotIn("FONTCONFIG_FILE", os.environ)
                self.assertTrue(Path(env["FONTCONFIG_FILE"]).is_file())
                self.assertFalse(metadata["system_fonts_modified"])
            with (
                patch(
                    "ppt_restore.rendering.renderers.platform.system",
                    return_value="Darwin",
                ),
                patch.dict(os.environ, {"FONTCONFIG_FILE": "/custom/fonts.conf"}),
            ):
                env, metadata = isolated_font_environment(directory)
                self.assertEqual(env["FONTCONFIG_FILE"], "/custom/fonts.conf")
                self.assertEqual(metadata["mode"], "inherited")

    def test_pdf_missing_chinese_is_rejected(self):
        from ppt_restore.rendering.renderers import check_pdf_cjk_preservation

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pptx = root / "input.pptx"
            with zipfile.ZipFile(pptx, "w") as archive:
                archive.writestr(
                    "ppt/slides/slide1.xml",
                    '<a:t xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">季度目标</a:t>',
                )
            for text, expected in [
                ("季季季季", "FAILED"),
                ("季度目标", "TEXT_PRESERVED"),
            ]:
                with patch(
                    "pypdf.PdfReader",
                    return_value=SimpleNamespace(
                        pages=[SimpleNamespace(extract_text=lambda: text)]
                    ),
                ):
                    report = check_pdf_cjk_preservation(pptx, root / "out.pdf")
                self.assertEqual(report["status"], expected)

    def test_old_pdf_cannot_mask_failed_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pptx = root / "input.pptx"
            pptx.write_bytes(b"input")
            out = root / "render"
            out.mkdir()
            old = out / "input.pdf"
            old.write_bytes(b"old successful export")
            with (
                patch(
                    "ppt_restore.rendering.renderers.subprocess.run",
                    return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                ),
                patch("ppt_restore.rendering.renderers._rasterize_pdf") as raster,
            ):
                result = LibreOfficeBackend(executable="/bin/true").render(pptx, out)
            self.assertFalse(result.success)
            raster.assert_not_called()
            self.assertEqual(old.read_bytes(), b"old successful export")

    def test_missing_input_is_a_failed_render(self):
        with tempfile.TemporaryDirectory() as temp:
            result = LibreOfficeBackend().render(
                Path(temp) / "missing.pptx", Path(temp) / "out"
            )
        self.assertFalse(result.success)
        self.assertFalse(result.acceptance_eligible)
        self.assertIn("does not exist", result.error)

    def test_libreoffice_uses_capability_detection(self):
        backend = LibreOfficeBackend(executable="definitely-not-a-real-soffice")
        self.assertFalse(backend.available)

    def test_powerpoint_is_not_claimed_on_unsupported_host(self):
        backend = PowerPointBackend()
        if backend.system not in ("Windows", "Darwin"):
            self.assertFalse(backend.available)

    def test_wps_installed_is_distinct_from_headless_capability(self):
        backend = WpsBackend(
            app_path="/Applications/wpsoffice.app", executable="/nonexistent/wpscli"
        )
        self.assertTrue(backend.installed)
        self.assertFalse(backend.headless_available)
        self.assertFalse(backend.available)

    def test_wps_reads_bundle_version_from_info_plist(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "WPS.app"
            info = app / "Contents" / "Info.plist"
            info.parent.mkdir(parents=True)
            with info.open("wb") as stream:
                plistlib.dump(
                    {"CFBundleShortVersionString": "12.3.4", "CFBundleVersion": "1234"},
                    stream,
                )
            self.assertEqual(read_wps_version(app), "12.3.4")
            backend = WpsBackend(app_path=str(app), executable="/nonexistent/wpscli")
            self.assertFalse(backend.available)

    def test_imported_wps_pdf_is_preverification_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pptx = root / "input.pptx"
            source_pdf = root / "exported.pdf"
            output = root / "render"
            pptx.write_bytes(b"pptx-fixture")
            source_pdf.write_bytes(b"%PDF-1.4 fixture")
            with patch(
                "ppt_restore.rendering.renderers._rasterize_pdf",
                return_value=[str(output / "slide-1.png")],
            ):
                result = WpsBackend(exported_pdf=source_pdf).render(pptx, output)
        self.assertTrue(result.success)
        self.assertEqual(result.status, "PREVERIFIED")
        self.assertFalse(result.acceptance_eligible)
        self.assertEqual(result.metadata["wps_mode"], "imported_pdf")
        self.assertTrue(result.metadata["imported_pdf"])


if __name__ == "__main__":
    unittest.main()
