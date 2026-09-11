import unittest

from ppt_restore.contracts.schema_v2 import SceneNode, SceneSpecV2
from ppt_restore.quality.optimizer import Optimizer


class OptimizerCoreTests(unittest.TestCase):
    def test_issue_priority_reaches_later_nodes_with_small_budget(self):
        scene = {
            "nodes": [
                {"id": "first", "block_id": "b", "bbox_px": [0, 0, 20, 20]},
                {"id": "problem", "block_id": "b", "bbox_px": [0, 0, 20, 20]},
            ]
        }
        result = Optimizer(max_rounds=1, max_candidates=2).optimize(
            scene,
            "b",
            lambda candidate: abs(candidate["nodes"][1]["bbox_px"][0] - 16),
            priority_node_ids=["outside-scope", "problem"],
        )
        self.assertEqual(result.best_loss, 0)
        self.assertEqual(result.scene["nodes"][0], scene["nodes"][0])

    def test_line_spacing_uses_fractional_steps_and_preserves_content(self):
        scene = {
            "nodes": [
                {
                    "id": "text",
                    "block_id": "b",
                    "style": {"line_spacing": 1.0},
                    "payload": {"text": "季度目标 38万"},
                }
            ]
        }
        result = Optimizer(max_rounds=1).optimize(
            scene,
            "b",
            lambda candidate: abs(
                candidate["nodes"][0]["style"]["line_spacing"] - 1.16
            ),
            variables=["line_spacing"],
        )
        self.assertAlmostEqual(result.scene["nodes"][0]["style"]["line_spacing"], 1.16)
        self.assertEqual(
            result.scene["nodes"][0]["payload"], scene["nodes"][0]["payload"]
        )

    def test_failed_baseline_aborts_but_failed_trial_is_rejected(self):
        scene = {
            "blocks": [
                {"id": "b", "elements": [{"id": "e", "layout_bbox_px": [0, 0, 10, 10]}]}
            ]
        }

        def failure(_):
            raise ValueError("renderer unavailable")

        with self.assertRaisesRegex(ValueError, "renderer unavailable"):
            Optimizer().optimize(scene, "b", failure)

        def objective(candidate):
            x = candidate["blocks"][0]["elements"][0]["layout_bbox_px"][0]
            if x < 0:
                raise ValueError("outside canvas")
            return abs(x - 16)

        result = Optimizer().optimize(scene, "b", objective)
        self.assertEqual(result.best_loss, 0)
        self.assertTrue(any("candidate_rejected" in item for item in result.history))

    def test_missing_objective_and_unknown_block_are_rejected(self):
        with self.assertRaises(ValueError):
            Optimizer().optimize({}, "missing")
        with self.assertRaises(ValueError):
            Optimizer().optimize(
                {"nodes": [{"id": "a", "block_id": "other"}]}, "missing", lambda _: 0
            )
        with self.assertRaisesRegex(ValueError, "missing a numeric loss"):
            Optimizer().optimize(
                {"nodes": [{"id": "a", "block_id": "b"}]},
                "b",
                lambda _: {"error": "failed"},
            )

    def test_owned_nodes_exclude_other_blocks_and_background(self):
        scene = {
            "nodes": [
                {"id": "a", "block_id": "b", "bbox_px": [0, 0, 20, 20]},
                {"id": "other", "block_id": "c", "bbox_px": [0, 0, 20, 20]},
                {"id": "background", "bbox_px": [0, 0, 100, 100]},
            ]
        }
        result = Optimizer().optimize(
            scene, "b", lambda s: abs(s["nodes"][0]["bbox_px"][0] - 16)
        )
        self.assertEqual(result.scene["nodes"][1:], scene["nodes"][1:])

    def test_coordinate_search_cache_and_stop(self):
        scene = {
            "blocks": [
                {
                    "id": "b",
                    "elements": [{"id": "e", "layout_bbox_px": [0, 0, 100, 100]}],
                }
            ]
        }
        calls = []

        def objective(candidate):
            calls.append(candidate)
            return abs(candidate["blocks"][0]["elements"][0]["layout_bbox_px"][0] - 16)

        result = Optimizer(max_rounds=5, max_candidates=32).optimize(
            scene, "b", objective
        )
        self.assertTrue(result.improved)
        self.assertLessEqual(result.rounds, 5)
        self.assertLessEqual(result.candidates_evaluated, 5 * 32)
        self.assertIn(
            result.stopped_reason, ("two_consecutive_rounds_below_0.2%", "max_rounds")
        )
        self.assertEqual(
            result.scene["blocks"][0]["elements"][0]["layout_bbox_px"][0], 16
        )
        # Explicit cache API is also used by render backends that batch
        # equivalent candidates.
        optimizer = Optimizer()
        optimizer.cached_evaluate(scene, lambda _: 3.0)
        optimizer.cached_evaluate(scene, lambda _: 3.0)
        self.assertEqual(optimizer.cache_hits, 1)

    def test_variable_whitelist_excludes_unknown_fields(self):
        scene = {
            "blocks": [
                {
                    "id": "b",
                    "elements": [
                        {"id": "e", "layout_bbox_px": [0, 0, 100, 100], "secret": 99}
                    ],
                }
            ]
        }
        result = Optimizer().optimize(
            scene, "b", lambda candidate: 1.0, variables=["secret"]
        )
        self.assertFalse(result.improved)
        self.assertEqual(result.scene["blocks"][0]["elements"][0]["secret"], 99)

    def test_v2_nodes_can_be_optimized_without_mutating_the_source(self):
        scene = SceneSpecV2(
            "2.0",
            "a" * 64,
            "b" * 64,
            {"width_px": 1440, "height_px": 810},
            (
                SceneNode(
                    "title",
                    "text",
                    "title",
                    (0, 0, 100, 40),
                    payload={"text": "x"},
                    confidence=1.0,
                    block_id="slide",
                ),
            ),
            state="VALIDATED",
            blocks=({"id": "slide", "bbox_norm": [0, 0, 1000, 1000]},),
        )
        result = Optimizer(max_rounds=1, max_candidates=4).optimize(
            scene, "slide", lambda candidate: abs(candidate.nodes[0].bbox_px[0] - 16)
        )
        self.assertTrue(result.improved)
        self.assertEqual(scene.nodes[0].bbox_px[0], 0.0)


if __name__ == "__main__":
    unittest.main()
