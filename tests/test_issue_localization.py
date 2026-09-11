import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.quality.issue_localization import localize_issues


class LocalizationTests(unittest.TestCase):
    def test_local_evidence_ids_scope_and_safe_paths(self):
        scene = SceneSpecV2(
            "2.0",
            "a" * 64,
            "b" * 64,
            {"width_px": 200, "height_px": 100},
            (
                SceneNode(
                    "../text",
                    "text",
                    "body",
                    (10, 10, 40, 20),
                    block_id="b1",
                    payload={"text": "中文"},
                ),
                SceneNode(
                    "other",
                    "text",
                    "body",
                    (110, 10, 40, 20),
                    block_id="b2",
                    payload={"text": "其他"},
                ),
            ),
            blocks=(
                {"id": "b1", "bbox_norm": [0, 0, 500, 1000]},
                {"id": "b2", "bbox_norm": [500, 0, 500, 1000]},
            ),
        )
        source = Image.new("RGB", (200, 100), "white")
        actual = source.copy()
        ImageDraw.Draw(actual).rectangle((10, 10, 49, 29), fill="black")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issues = localize_issues(
                scene, "b1", source, actual, root, "scene-hash", "ppt-hash"
            )
            self.assertEqual(len(issues), 1)
            issue = issues[0]
            self.assertEqual(issue["node_id"], "../text")
            self.assertEqual(issue["scene_sha256"], "scene-hash")
            self.assertEqual(issue["measurement"]["mean_absolute_rgb_error"], 1)
            for path in issue["evidence"].values():
                self.assertTrue(Path(path).is_file())
                self.assertTrue(Path(path).resolve().is_relative_to(root.resolve()))
            self.assertEqual(
                localize_issues(scene, "b1", source, source, root, "s", "p"), []
            )
