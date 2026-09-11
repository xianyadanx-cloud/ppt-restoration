"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.cli.services import _backend


def run(args):
    from ppt_restore.quality.render_probe import run_render_probe

    report = run_render_probe(_backend(args.renderer), args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["automatic_optimization_allowed"] else 1
