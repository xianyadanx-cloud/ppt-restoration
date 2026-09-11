"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json


def run(args):
    from ppt_restore.pipeline.block_gate import approve_block

    print(
        json.dumps(
            approve_block(
                args.case_dir,
                args.block_id,
                args.review_report,
                user_confirmed=args.user_confirmed,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
