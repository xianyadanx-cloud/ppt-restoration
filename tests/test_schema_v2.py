import hashlib
import json
import unittest

from ppt_restore.contracts.schema_v2 import (
    EvidenceBundle,
    NodeKind,
    RenderOp,
    RenderPlan,
    RenderStrategy,
    SceneNode,
    SceneSpecV2,
    SemanticRole,
    evidence_sha256,
    scene_sha256,
)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SceneSpecV2Tests(unittest.TestCase):
    def setUp(self):
        self.canvas = {
            "width_px": 1440,
            "height_px": 810,
            "color_space": "sRGB",
            "dpi": 96.0,
        }
        self.canonical = digest("canonical")
        self.evidence = digest("evidence")

    def test_round_trip_and_hashes_are_stable(self):
        node = SceneNode(
            id="title",
            kind=NodeKind.TEXT.value,
            role=SemanticRole.TITLE.value,
            bbox_px=(20, 20, 400, 50),
            payload={"text": "季度策略"},
            style={"font_size_pt": 28},
            render_strategy=RenderStrategy.NATIVE.value,
        )
        scene = SceneSpecV2("2.0", self.canonical, self.evidence, self.canvas, (node,))
        decoded = SceneSpecV2.from_json(scene.to_json())
        self.assertEqual(decoded, scene)
        self.assertEqual(scene_sha256(scene), digest(scene.to_json()))
        bundle = EvidenceBundle("1.0", self.canonical, self.canvas)
        self.assertEqual(evidence_sha256(bundle), digest(bundle.to_json()))

    def test_unknown_fields_and_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            SceneNode.from_dict(
                {
                    "id": "x",
                    "kind": "text",
                    "role": "title",
                    "bbox_px": [0, 0, 10, 10],
                    "payload": {"text": "x"},
                    "unknown": 1,
                }
            )
        node = {
            "id": "x",
            "kind": "shape",
            "role": "container",
            "bbox_px": [0, 0, 10, 10],
        }
        with self.assertRaises(ValueError):
            SceneSpecV2.from_dict(
                {
                    "schema_version": "2.0",
                    "canonical_sha256": self.canonical,
                    "evidence_sha256": self.evidence,
                    "canvas": self.canvas,
                    "nodes": [node, node],
                }
            )

    def test_parent_cycles_and_out_of_canvas_fail(self):
        parent = SceneNode("p", "group", "container", (0, 0, 100, 100))
        child = SceneNode("c", "shape", "decoration", (10, 10, 20, 20), parent_id="p")
        self.assertEqual(
            SceneSpecV2(
                "2.0", self.canonical, self.evidence, self.canvas, (parent, child)
            )
            .nodes[1]
            .parent_id,
            "p",
        )
        with self.assertRaises(ValueError):
            SceneSpecV2(
                "2.0",
                self.canonical,
                self.evidence,
                self.canvas,
                (SceneNode("x", "shape", "decoration", (1430, 0, 20, 20)),),
            )
        with self.assertRaises(ValueError):
            SceneSpecV2(
                "2.0",
                self.canonical,
                self.evidence,
                self.canvas,
                (
                    SceneNode(
                        "a", "group", "container", (0, 0, 100, 100), parent_id="b"
                    ),
                    SceneNode(
                        "b", "group", "container", (0, 0, 100, 100), parent_id="a"
                    ),
                ),
            )

    def test_component_payload_contracts(self):
        with self.assertRaises(ValueError):
            SceneNode("t", "text", "title", (0, 0, 100, 20))
        with self.assertRaises(ValueError):
            SceneNode("i", "image", "decoration", (0, 0, 100, 20))
        with self.assertRaises(ValueError):
            SceneNode("c", "chart", "chart", (0, 0, 100, 20), payload={})

    def test_public_normalized_box_is_converted_at_ingest(self):
        payload = {
            "schema_version": "2.0",
            "canonical_sha256": self.canonical,
            "evidence_sha256": self.evidence,
            "canvas": {"width_px": 1440, "height_px": 810},
            "nodes": [
                {
                    "id": "title",
                    "kind": "text",
                    "role": "title",
                    "bbox_norm": [100, 100, 200, 100],
                    "payload": {"text": "标题"},
                }
            ],
        }
        scene = SceneSpecV2.from_dict(payload)
        self.assertEqual(scene.nodes[0].bbox_px, (144.0, 81.0, 288.0, 81.0))

    def test_render_plan_round_trip(self):
        op = RenderOp(
            "title", "text", (20, 20, 400, 50), payload={"text": "季度策略"}, style={}
        )
        plan = RenderPlan("1.0", self.canonical, self.canvas, (op,), ("warning",))
        self.assertEqual(
            RenderPlan("1.0", self.canonical, self.canvas, (op,), ("warning",)), plan
        )
        self.assertEqual(json.loads(plan.to_json())["operations"][0]["op_type"], "text")


if __name__ == "__main__":
    unittest.main()
