"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json

from ppt_restore.pipeline.workflow import ingest_scene


def run(args):
    result = ingest_scene(
        args.case_dir,
        args.scene_proposed,
        content_audit_path=args.content_audit,
        allow_missing_audit=args.allow_missing_audit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "VALIDATED" else 1
