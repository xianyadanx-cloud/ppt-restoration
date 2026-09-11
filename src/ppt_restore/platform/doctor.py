"""Environment capability matrix for reproducible restoration runs."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from ppt_restore.platform.ocr import auto_ocr_providers
from ppt_restore.rendering.renderers import (
    _wps_supports_ppt2pdf,
    find_wps,
    find_wps_cli,
    read_wps_version,
)


@dataclass(frozen=True)
class DoctorReport:
    python: str
    platform: str
    dependencies: Mapping[str, Optional[str]]
    fonts: Mapping[str, Any]
    renderers: Mapping[str, bool]
    capabilities: Mapping[str, Any]
    ok: bool = True

    def to_dict(self):
        return {
            "python": self.python,
            "platform": self.platform,
            "dependencies": dict(self.dependencies),
            "fonts": dict(self.fonts),
            "renderers": dict(self.renderers),
            "capabilities": dict(self.capabilities),
            "ok": self.ok,
        }

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, **kwargs)


def _version(name, module=None):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        try:
            m = importlib.import_module(module or name)
            return getattr(m, "__version__", "installed")
        except Exception:
            return None


def _font_inventory():
    roots = []
    if sys.platform == "darwin":
        roots.extend(
            (
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path.home() / "Library/Fonts",
            )
        )
    elif os.name == "nt":
        roots.extend(
            (
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
            )
        )
    else:
        roots.extend(
            (
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
            )
        )
    files = []
    for root in roots:
        if root.exists():
            files.extend(
                str(p)
                for p in root.rglob("*")
                if p.suffix.lower() in (".ttf", ".otf", ".ttc")
            )
    return {
        "search_paths": [str(x) for x in roots],
        "count": len(files),
        "fonttools": _version("fonttools", "fontTools"),
        "files": sorted(files)[:2000],
    }


def _ocr_inventory() -> Dict[str, Any]:
    """Describe OCR discovery without claiming that execution succeeded."""

    providers = []
    for provider in auto_ocr_providers():
        name = str(getattr(provider, "name", provider.__class__.__name__.lower()))
        language = getattr(provider, "language", None)
        label = "%s[%s]" % (name, language) if language else name
        try:
            available = bool(provider.available)
            status = "available" if available else "unavailable"
            error = None
        except Exception as exc:
            available = False
            status = "probe_failed"
            error = "%s: %s" % (
                exc.__class__.__name__,
                str(exc).strip() or "unknown error",
            )
        details = {
            "name": name,
            "label": label,
            "available": available,
            "status": status,
        }
        if error:
            details["error"] = error
        executable = getattr(provider, "swift", None) or getattr(
            provider, "executable", None
        )
        script = getattr(provider, "script", None)
        if executable:
            details["executable"] = str(executable)
        if script:
            details["script"] = str(script)
        providers.append(details)
    available = [item for item in providers if item["available"]]
    # Discovery only proves that a provider can be located.  It does not prove
    # that OCR will run successfully on this image (Vision can fail later due
    # to a compiler/SDK mismatch, for example).  ``prepare`` performs the
    # runtime check and records its result in evidence.json.
    return {
        "status": "discovered_unverified" if available else "degraded",
        "available": bool(available),
        "provider_count": len(providers),
        "providers": providers,
        "runtime_validation": "not_run; prepare records execution failures in evidence.json",
    }


def doctor() -> DoctorReport:
    deps = {
        "Pillow": _version("Pillow", "PIL"),
        "python-pptx": _version("python-pptx", "pptx"),
        "pypdf": _version("pypdf"),
        "fonttools": _version("fonttools", "fontTools"),
        "numpy": _version("numpy"),
        "wps": None,
    }
    # FontTools and OCR are quality cross-checks, not requirements for the
    # canonical-image -> SceneSpec -> native-PPT workflow.  Keep this list in
    # lockstep with the core ``dependencies`` in pyproject.toml.
    required_core = ("Pillow", "python-pptx", "pypdf")
    missing_core = [name for name in required_core if not deps.get(name)]
    core_status = (
        "available"
        if not missing_core
        else "blocked: missing required package(s): %s" % ", ".join(missing_core)
    )
    runtime_core = all(deps.get(name) for name in ("Pillow", "python-pptx", "pypdf"))
    try:
        from ppt_restore.contracts.schema_v2 import SceneSpecV2  # noqa: F401
        from ppt_restore.pipeline.workflow import (  # noqa: F401
            ingest_scene,
            prepare_case,
        )

        multimodal_contract_status = (
            "available" if runtime_core else "blocked: core runtime unavailable"
        )
    except (
        Exception
    ) as exc:  # pragma: no cover - import failures are environment-specific
        multimodal_contract_status = "blocked: %s: %s" % (
            exc.__class__.__name__,
            str(exc).strip() or "contract import failed",
        )
    ocr = _ocr_inventory()
    wps_app = find_wps()
    wps_cli = find_wps_cli(wps_app)
    wps_headless = _wps_supports_ppt2pdf(wps_cli)
    deps["wps"] = read_wps_version(wps_app)
    pdf_rasterizer = bool(
        shutil.which("pdftoppm") or shutil.which("magick") or shutil.which("convert")
    )
    renderers = {
        "libreoffice": bool(shutil.which("libreoffice") or shutil.which("soffice")),
        "powerpoint": bool(
            shutil.which("powerpnt")
            or (
                sys.platform == "win32"
                and Path(
                    os.environ.get("PROGRAMFILES", "C:/Program Files"),
                    "Microsoft Office",
                ).exists()
            )
            or (
                sys.platform == "darwin"
                and Path("/Applications/Microsoft PowerPoint.app").exists()
            )
        ),
        "wps_installed": bool(wps_app),
        "wps_headless": wps_headless,
        "wps_pdf_import": pdf_rasterizer,
    }
    capabilities = {
        # Keep core execution and optional acceptance capabilities separate.
        # A missing OCR engine or PowerPoint installation must not be reported
        # as a missing/failed deterministic core runtime, and vice versa.
        "core": core_status,
        "core_runtime": "available"
        if runtime_core
        else "blocked: missing Pillow/python-pptx/pypdf",
        "multimodal_contract": multimodal_contract_status,
        "canonicalize": "available" if deps["Pillow"] else "missing Pillow",
        "evidence": "available" if deps["Pillow"] else "missing Pillow",
        "semantic_scene_v2": "available"
        if runtime_core
        else "blocked: missing core dependency",
        "font_strict_validation": "available"
        if deps["fonttools"]
        else "degraded: fonttools unavailable; strict glyph/font measurement disabled",
        # Backwards-compatible alias retained for callers that used the old
        # capability name.  It intentionally carries the same optional state.
        "font_measurement": "available"
        if deps["fonttools"]
        else "degraded: missing optional fonttools",
        "agent_boundary": "prepare + ingest",
        "ocr_crosscheck": "discovered_unverified: provider discovery only; prepare validates execution"
        if ocr["available"]
        else "degraded: no local OCR provider; canonical image remains authoritative",
        "ocr": "discovered_unverified: provider discovery only"
        if ocr["available"]
        else "degraded: no local provider",
        "ocr_provider_count": ocr["provider_count"],
        "native_vector_build": "available"
        if runtime_core
        else "missing core dependency",
        "preverify": "available"
        if renderers["libreoffice"]
        else "renderer unavailable",
        "wps_preverify": "headless"
        if wps_headless
        else "imported PDF via --wps-pdf"
        if pdf_rasterizer
        else "WPS/PDF rasterizer unavailable",
        "formal_pass": "available"
        if renderers["powerpoint"]
        else "blocked: PowerPoint required",
        "formal_powerpoint_acceptance": "available"
        if renderers["powerpoint"]
        else "blocked: PowerPoint required",
    }
    # ``ok`` answers whether the multimodal core can execute.  Optional
    # cross-checks and formal PowerPoint acceptance are reported independently
    # above and must not make a healthy core environment look unusable.
    ok = runtime_core and multimodal_contract_status == "available"
    return DoctorReport(
        sys.version.split()[0],
        platform.platform(),
        deps,
        _font_inventory(),
        renderers,
        {
            **capabilities,
            "ocr_details": ocr,
            "core_required_dependencies": list(required_core),
            "core_missing_dependencies": missing_core,
            "optional_dependencies": {
                "ocr": "pytesseract + system tesseract executable (optional)",
                "font_strict": "fonttools>=4.0 (optional)",
            },
        },
        ok,
    )


def main(argv=None):
    print(doctor().to_json(indent=2))
    return 0
