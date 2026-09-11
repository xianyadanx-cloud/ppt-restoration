"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

import json
from pathlib import Path


def run(args):
    from ppt_restore.rendering.renderers import (
        AutoRenderBackend,
        LibreOfficeBackend,
        PowerPointBackend,
        WpsBackend,
    )

    if args.renderer == "wps":
        backend = WpsBackend(exported_pdf=args.wps_pdf)
    elif args.renderer == "auto":
        backend = AutoRenderBackend(wps_pdf=args.wps_pdf)
    else:
        backend = {"powerpoint": PowerPointBackend, "libreoffice": LibreOfficeBackend}[
            args.renderer
        ]()
    out = args.output_dir or str(Path(args.pptx).with_suffix("")) + "_render"
    result = backend.render(args.pptx, out)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1
