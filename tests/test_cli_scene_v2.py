import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ppt_restore.cli import main
from ppt_restore.contracts.schema_v2 import SceneSpecV2
from ppt_restore.platform.provenance import sha256_file


class CliSceneV2Tests(unittest.TestCase):
    def test_pipeline_stops_for_agent_scene_then_build_accepts_ingested_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            Image.new("RGB", (1440, 810), "white").save(source)
            case = root / "case"
            output = root / "slide.pptx"

            self.assertEqual(
                main(
                    [
                        "pipeline",
                        str(source),
                        "--case-dir",
                        str(case),
                        "--output",
                        str(output),
                        "--ocr",
                        "none",
                    ]
                ),
                0,
            )
            self.assertFalse(output.exists())
            scene = SceneSpecV2(
                "2.0",
                sha256_file(case / "canonical.png"),
                sha256_file(case / "evidence.json"),
                {"width_px": 1440, "height_px": 810},
                (),
            )
            proposed = case / "scene.proposed.json"
            proposed.write_text(scene.to_json(), encoding="utf-8")
            self.assertEqual(main(["ingest", str(case), str(proposed)]), 1)
            self.assertFalse((case / "scene.json").exists())
            self.assertEqual(
                main(["ingest", str(case), str(proposed), "--allow-missing-audit"]), 0
            )
            self.assertEqual(
                main(
                    [
                        "pipeline",
                        str(source),
                        "--case-dir",
                        str(case),
                        "--output",
                        str(output),
                        "--ocr",
                        "none",
                    ]
                ),
                1,
            )
            self.assertEqual(main(["build", str(case), "--output", str(output)]), 0)
            self.assertTrue(output.is_file())
            self.assertTrue((case / "builds").is_dir())
            # LibreOffice is a pre-verifier on this host; it must still emit
            # a manifest-backed, structured verification report.
            from ppt_restore.rendering.renderers import LibreOfficeBackend

            if LibreOfficeBackend().available and shutil.which("pdftoppm"):
                self.assertEqual(
                    main(
                        ["verify", str(case), str(output), "--renderer", "libreoffice"]
                    ),
                    0,
                )
                self.assertTrue((case / "reports" / "verification.json").is_file())


if __name__ == "__main__":
    unittest.main()
