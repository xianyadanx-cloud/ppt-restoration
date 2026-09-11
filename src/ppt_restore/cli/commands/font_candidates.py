"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json


def run(args):
    from ppt_restore.rendering.fonts import FontRegistry

    result = FontRegistry().rank_candidates(
        args.text, args.size_pt, args.width_pt, args.weight
    )
    print(
        json.dumps(
            {"candidates": result, "status": "VISUAL_CONFIRMATION_REQUIRED"},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
