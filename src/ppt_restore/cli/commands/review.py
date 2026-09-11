"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.cli.services import _backend


def run(args):
    from ppt_restore.quality.review import review_block

    report = review_block(
        args.case_dir, args.block, _backend(args.renderer, args.wps_pdf), args.pptx
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "REVIEW_READY" else 1
