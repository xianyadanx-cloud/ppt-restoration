"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json


def run(args):
    from ppt_restore.pipeline.block_gate import read_block_gate

    gate = read_block_gate(args.case_dir)
    print(
        json.dumps(gate or {"status": "NOT_INITIALIZED"}, ensure_ascii=False, indent=2)
    )
    return 0
