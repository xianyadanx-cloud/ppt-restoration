"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json


def run(args):
    from ppt_restore.pipeline.host_tasks import next_task

    print(json.dumps(next_task(args.case_dir), ensure_ascii=False, indent=2))
    return 0
