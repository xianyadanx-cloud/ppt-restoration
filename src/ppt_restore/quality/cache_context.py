"""Explicit inputs to visual-score caching, independent of candidate geometry."""

import hashlib
import json
import os
import platform
from pathlib import Path

from ppt_restore.platform.provenance import sha256_file
from ppt_restore.rendering.fonts import _platform_font_dirs


def visual_cache_context(reference, renderer, evaluation, font_dirs=None):
    fonts = []
    for root in font_dirs if font_dirs is not None else _platform_font_dirs():
        root = Path(root)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {
                ".ttf",
                ".ttc",
                ".otf",
                ".otc",
            }:
                fonts.append([str(path.resolve()), sha256_file(path)])
    config = os.environ.get("FONTCONFIG_FILE")
    code = Path(__file__).resolve().parents[1]
    return {
        "reference_sha256": sha256_file(reference),
        "renderer": renderer,
        "evaluation": evaluation,
        "platform": platform.platform(),
        "font_files_sha256": hashlib.sha256(
            json.dumps(fonts, sort_keys=True).encode()
        ).hexdigest(),
        "font_file_count": len(fonts),
        "fontconfig": {
            "path": config,
            "sha256": sha256_file(config)
            if config and Path(config).is_file()
            else None,
        },
        "implementation": {
            name: sha256_file(code / name)
            for name in (
                "rendering/renderers.py",
                "quality/visual_objective.py",
                "rendering/compiler.py",
                "rendering/scene_v2_compiler.py",
            )
        },
    }
