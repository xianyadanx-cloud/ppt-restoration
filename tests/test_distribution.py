"""Distribution contracts: package resources and a non-repository case path."""

import contextlib
import io
import json
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from PIL import Image

from ppt_restore.cli import COMMANDS, main
from ppt_restore.platform.io import read_scene_any
from ppt_restore.platform.ocr import MacVisionOcrProvider


class DistributionTests(unittest.TestCase):
    def test_all_command_help_parsers(self):
        with contextlib.redirect_stdout(io.StringIO()):
            for command in COMMANDS:
                with (
                    self.subTest(command=command),
                    self.assertRaises(SystemExit) as result,
                ):
                    main([command, "--help"])
                self.assertEqual(result.exception.code, 0)

    def test_prepare_exports_packaged_prompt_and_ocr_script_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "case with spaces"
            root.mkdir()
            source = root / "source.png"
            Image.new("RGB", (1600, 900), "white").save(source)
            case = root / "case"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "prepare",
                            str(source),
                            "--case-dir",
                            str(case),
                            "--ocr",
                            "none",
                        ]
                    ),
                    0,
                )
            request = json.loads(
                (case / "agent_request.json").read_text(encoding="utf-8")
            )
            prompt = Path(request["prompt_template"])
            self.assertEqual(prompt.parent, case.resolve())
            self.assertEqual(
                prompt.read_text(encoding="utf-8"),
                files("ppt_restore")
                .joinpath("resources", "scene_spec_v2.md")
                .read_text(encoding="utf-8"),
            )
            self.assertIn("Pass 2", prompt.read_text(encoding="utf-8"))
            self.assertTrue(Path(MacVisionOcrProvider().script).is_file())

    def test_obsolete_scene_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "scene.json").write_text(
                '{"schema_version": "1.0"}', encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Only SceneSpec v2"):
                read_scene_any(directory)
