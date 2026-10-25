"""``pptrestore preview``: render a proposed scene and diff it against canonical.png."""

import json


def run(args):
    from ppt_restore.quality.preview import preview_scene

    report = preview_scene(args.case_dir, args.scene, args.output_dir, renderer=args.renderer)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "RENDERED" else 1
