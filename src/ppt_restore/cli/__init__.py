"""Command-line entry point."""

import importlib
import json
import sys

from .parser import _parser

COMMANDS = {
    "font-candidates": "font_candidates",
    "next": "next",
    "blueprint": "blueprint",
    "revise": "revise",
    "review": "review",
    "doctor": "doctor",
    "render-probe": "render_probe",
    "block-init": "block_init",
    "block-status": "block_status",
    "block-approve": "block_approve",
    "canonicalize": "canonicalize",
    "prepare": "prepare",
    "ingest": "ingest",
    "build": "build",
    "render": "render",
    "verify": "verify",
    "optimize": "optimize",
    "pipeline": "pipeline",
}


def _main(argv=None):
    args = _parser().parse_args(argv)
    module = importlib.import_module(
        "ppt_restore.cli.commands." + COMMANDS[args.command]
    )
    return module.run(args)


def main(argv=None):
    try:
        return _main(argv)
    except (FileNotFoundError, ValueError, IndexError) as exc:
        print(
            json.dumps(
                {"status": "INVALID_INPUT", "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, RuntimeError) as exc:
        print(
            json.dumps(
                {"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2
            ),
            file=sys.stderr,
        )
        return 1
