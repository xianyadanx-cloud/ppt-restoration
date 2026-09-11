import tempfile
import unittest
from pathlib import Path

from ppt_restore.quality.build_manifest import (
    create_build_manifest,
    find_build_manifest,
    validate_build_manifest,
)


class BuildManifestTests(unittest.TestCase):
    def test_manifest_binds_all_inputs_and_detects_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {}
            for name, value in (
                ("canonical.png", b"canonical"),
                ("evidence.json", b"evidence"),
                ("scene.json", b"scene"),
                ("render_plan.json", b"plan"),
                ("result.pptx", b"pptx"),
            ):
                path = root / name
                path.write_bytes(value)
                files[name] = path
            manifest, target = create_build_manifest(
                root / "case",
                files["result.pptx"],
                canonical_path=files["canonical.png"],
                evidence_path=files["evidence.json"],
                scene_path=files["scene.json"],
                render_plan_path=files["render_plan.json"],
            )
            self.assertTrue(target.is_file())
            found = find_build_manifest(root / "case", files["result.pptx"])
            self.assertIsNotNone(found)
            result = validate_build_manifest(
                manifest,
                canonical_path=files["canonical.png"],
                evidence_path=files["evidence.json"],
                scene_path=files["scene.json"],
                render_plan_path=files["render_plan.json"],
                pptx_path=files["result.pptx"],
            )
            self.assertTrue(result["valid"])
            files["scene.json"].write_bytes(b"changed")
            result = validate_build_manifest(
                manifest,
                canonical_path=files["canonical.png"],
                evidence_path=files["evidence.json"],
                scene_path=files["scene.json"],
                render_plan_path=files["render_plan.json"],
                pptx_path=files["result.pptx"],
            )
            self.assertFalse(result["valid"])
            self.assertIn("scene_sha256 mismatch", result["mismatches"])


if __name__ == "__main__":
    unittest.main()
