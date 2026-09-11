import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from ppt_restore.quality.visual_objective import FixedRegionObjective


class FixedObjectiveTests(unittest.TestCase):
    def test_fixed_region_ignores_other_blocks_and_retains_text_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Image.new("RGB", (200, 100), "white")
            ImageDraw.Draw(source).rectangle((20, 20, 39, 39), fill="black")
            source.save(root / "reference.png")
            objective = FixedRegionObjective(
                root / "reference.png", [0, 0, 500, 1000], [[100, 200, 100, 200]]
            )
            self.assertEqual(objective.evaluate(root / "reference.png")["loss"], 0)
            other = source.copy()
            ImageDraw.Draw(other).rectangle((100, 0, 199, 99), fill="red")
            other.save(root / "other.png")
            self.assertEqual(objective.evaluate(root / "other.png")["loss"], 0)
            Image.new("RGB", source.size, "white").save(root / "missing.png")
            missing = objective.evaluate(root / "missing.png")
            self.assertEqual(missing["regional_losses"]["text"], 1)
            self.assertGreater(missing["loss"], 0.4)
            self.assertEqual(missing["reference_box_px"], [0, 0, 100, 100])

    def test_empty_region_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.png"
            Image.new("RGB", (100, 100), "white").save(path)
            with self.assertRaises(ValueError):
                FixedRegionObjective(path, [0, 0, 0, 100])
