import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.pipeline.block_gate import init_block_gate
from ppt_restore.pipeline.revisions import assert_ingest_scope, propose_revision
from ppt_restore.platform.provenance import sha256_file


class RevisionTests(unittest.TestCase):
    def test_local_structure_changes_and_cross_block_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocks = (
                {"id": "b1", "bbox_norm": [0, 0, 500, 1000]},
                {"id": "b2", "bbox_norm": [500, 0, 500, 1000]},
            )
            node = SceneNode(
                "a",
                "text",
                "body",
                (10, 10, 100, 30),
                block_id="b1",
                payload={"text": "旧文本"},
            )
            other = SceneNode(
                "b",
                "text",
                "body",
                (600, 10, 100, 30),
                block_id="b2",
                payload={"text": "锁定内容"},
            )
            scene = SceneSpecV2(
                "2.0",
                "a" * 64,
                "b" * 64,
                {"width_px": 1000, "height_px": 600},
                (node, other),
                blocks=blocks,
            )
            (root / "scene.json").write_text(scene.to_json(), encoding="utf-8")
            (root / "blueprint.json").write_text(
                json.dumps({"blocks": blocks}), encoding="utf-8"
            )
            init_block_gate(root, root / "blueprint.json")
            assert_ingest_scope(
                root,
                replace(scene, nodes=(replace(node, payload={"text": "修复"}), other)),
            )
            with self.assertRaisesRegex(ValueError, "another Block"):
                assert_ingest_scope(
                    root,
                    replace(
                        scene, nodes=(node, replace(other, payload={"text": "不允许"}))
                    ),
                )
            original = (root / "scene.json").read_bytes()
            added = dict(node.to_dict(), id="new", payload={"text": "补充 84%"})
            patch = {
                "base_scene_sha256": sha256_file(root / "scene.json"),
                "block_id": "b1",
                "additions": [added],
                "removals": ["a"],
            }
            path = root / "patch.json"
            path.write_text(json.dumps(patch), encoding="utf-8")
            result = propose_revision(root, path, root / "new.json")
            proposal = json.loads((root / "new.json").read_text(encoding="utf-8"))
            self.assertEqual(proposal["state"], "PROPOSED")
            self.assertEqual(
                next(n for n in proposal["nodes"] if n["id"] == "b"), other.to_dict()
            )
            self.assertEqual(result["changes"]["added"], ["new"])
            self.assertEqual((root / "scene.json").read_bytes(), original)
            for bad in (
                {"removals": ["b"]},
                {"additions": [dict(added, block_id="b2")]},
                {"additions": [dict(added, parent_id="b")]},
            ):
                path.write_text(
                    json.dumps(
                        dict(
                            base_scene_sha256=patch["base_scene_sha256"],
                            block_id="b1",
                            **bad,
                        )
                    ),
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    propose_revision(root, path, root / "bad.json")
                self.assertFalse((root / "bad.json").exists())
