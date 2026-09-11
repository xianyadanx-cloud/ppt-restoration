"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json


def run(args):
    from ppt_restore.pipeline.revisions import propose_revision

    print(
        json.dumps(
            propose_revision(args.case_dir, args.patch, args.output),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
