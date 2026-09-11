"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.cli.services import _verify


def run(args):
    payload, decision = _verify(
        args.case_dir, args.pptx, args.renderer, wps_pdf=args.wps_pdf
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if decision.status.value in ("PASS", "PREVERIFIED") else 1
