"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.pipeline.canonicalize import canonicalize


def run(args):
    result = canonicalize(
        args.input,
        args.case_dir,
        page_index=args.page_index,
        primary_renderer=args.primary_renderer,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0
