"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.cli.services import (
    _compile_scene,
    _reconcile_content_after_build,
    _set_manifest_state,
)
from ppt_restore.contracts.models import AnalysisState
from ppt_restore.platform.io import read_scene_any


def run(args):
    from ppt_restore.pipeline.block_gate import assert_build_allowed, record_block_build

    assert_build_allowed(args.case_dir, args.blocks)
    scene = read_scene_any(args.case_dir)
    result = _compile_scene(
        scene,
        args.case_dir,
        args.output,
        blocks=args.blocks,
        render_strategy=args.render_strategy,
    )
    _reconcile_content_after_build(
        result, args.case_dir, args.output, blocks=args.blocks
    )
    if args.blocks and not result.warnings:
        record_block_build(args.case_dir, args.blocks, args.output)
    elif args.blocks is None and not result.warnings:
        from ppt_restore.pipeline.host_tasks import record_full_build

        record_full_build(args.case_dir, args.output)
    _set_manifest_state(args.case_dir, AnalysisState.BUILT)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if not result.warnings else 1
