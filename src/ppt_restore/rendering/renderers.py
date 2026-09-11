"""Rendering backends.

PowerPoint is the acceptance renderer.  LibreOffice is deliberately only a
pre-verification backend. WPS also provides compatibility pre-verification.
"""

from __future__ import annotations

import abc
import os
import platform
import plistlib
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
from xml.etree import ElementTree

from ppt_restore.platform.provenance import environment_info, sha256_file

PathLike = Union[os.PathLike, str]


@dataclass
class RenderResult:
    """The complete, serialisable result of one render attempt."""

    backend: str
    success: bool
    output_dir: Optional[str] = None
    images: List[str] = field(default_factory=list)
    acceptance_eligible: bool = False
    status: str = "FAILED"
    error: Optional[str] = None
    pptx_sha256: Optional[str] = None
    renderer_version: Optional[str] = None
    os_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def rendered_images(self) -> List[str]:
        """Compatibility alias used by a few older callers."""

        return self.images

    @property
    def renderer(self) -> str:
        """Compatibility alias for callers that use the interface name."""

        return self.backend

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "success": self.success,
            "output_dir": self.output_dir,
            "images": list(self.images),
            "acceptance_eligible": self.acceptance_eligible,
            "status": self.status,
            "error": self.error,
            "pptx_sha256": self.pptx_sha256,
            "renderer_version": self.renderer_version,
            "os_info": dict(self.os_info),
            "metadata": dict(self.metadata),
        }


class RenderBackend(abc.ABC):
    """Common renderer contract."""

    name = "unknown"
    acceptance_eligible = False

    @property
    def available(self) -> bool:
        return True

    @abc.abstractmethod
    def render(self, pptx: PathLike, output_dir: PathLike) -> RenderResult:
        raise NotImplementedError

    def _failure(
        self, pptx: PathLike, output_dir: PathLike, message: str
    ) -> RenderResult:
        path = Path(pptx)
        return RenderResult(
            backend=self.name,
            success=False,
            output_dir=str(output_dir),
            acceptance_eligible=False,
            status="FAILED",
            error=message,
            pptx_sha256=sha256_file(path) if path.is_file() else None,
            os_info=environment_info(renderer=self.name),
        )

    def _invalid_input(
        self, pptx: PathLike, output_dir: PathLike
    ) -> Optional[RenderResult]:
        if not Path(pptx).is_file():
            return self._failure(
                pptx, output_dir, "PPTX input does not exist: %s" % pptx
            )
        return None


def _renderer_version(executable: Optional[str]) -> Optional[str]:
    if not executable:
        return None
    try:
        proc = subprocess.run(
            [executable, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            check=False,
        )
        return (proc.stdout or "").strip().splitlines()[0][:300] or None
    except (OSError, subprocess.SubprocessError):
        return None


def find_soffice() -> Optional[str]:
    """Locate LibreOffice without assuming a platform-specific install path."""

    env_path = os.environ.get("PPTRESTORE_SOFFICE") or os.environ.get("SOFFICE")
    if env_path and Path(env_path).is_file():
        return env_path
    for command in ("soffice", "libreoffice"):
        found = shutil.which(command)
        if found:
            return found
    # These are conventional application locations, not required paths.
    candidates = (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/local/bin/soffice",
        "/usr/bin/soffice",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return None


def find_wps() -> Optional[str]:
    env_path = os.environ.get("PPTRESTORE_WPS_APP")
    candidates = [env_path] if env_path else []
    candidates.extend(("/Applications/wpsoffice.app", "/Applications/WPS Office.app"))
    return next((path for path in candidates if path and Path(path).exists()), None)


def find_wps_cli(app_path: Optional[str] = None) -> Optional[str]:
    env_path = os.environ.get("PPTRESTORE_WPSCLI")
    if env_path and Path(env_path).is_file():
        return env_path
    app = app_path or find_wps()
    candidate = Path(app) / "Contents/MacOS/wpscli" if app else None
    return (
        str(candidate) if candidate and candidate.is_file() else shutil.which("wpscli")
    )


def _wps_supports_ppt2pdf(executable: Optional[str]) -> bool:
    if not executable:
        return False
    try:
        proc = subprocess.run(
            [executable, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and "ppt2pdf" in (proc.stdout or "")


def read_wps_version(app_path: Optional[PathLike]) -> Optional[str]:
    """Read WPS's bundle version without invoking macOS ``defaults``.

    Reading the plist directly is deterministic, works in CI without a GUI
    session, and also makes it straightforward for tests/doctor to inspect a
    fixture application bundle.  WPS has used both short and build version
    keys, so retain the first non-empty value in a stable order.
    """

    if not app_path:
        return None
    root = Path(app_path)
    candidates = [
        root if root.name == "Info.plist" else root / "Contents" / "Info.plist",
        root / "Info.plist",
    ]
    for plist_path in candidates:
        if not plist_path.is_file():
            continue
        try:
            with plist_path.open("rb") as stream:
                payload = plistlib.load(stream)
        except (OSError, plistlib.InvalidFileException, ValueError, TypeError):
            continue
        for key in (
            "CFBundleShortVersionString",
            "CFBundleVersion",
            "ProductVersion",
            "Version",
        ):
            value = payload.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return None


def _file_uri(path: Path) -> str:
    # A path under /tmp becomes file:///tmp/... as required by LO.
    return "file://" + path.resolve().as_posix()


def check_pdf_cjk_preservation(pptx, pdf):
    """A necessary text-survival check, never proof of correct glyph drawing."""

    def cjk(text):
        return Counter(ch for ch in text if "\u3400" <= ch <= "\u9fff")

    with zipfile.ZipFile(pptx) as package:
        text = "".join(
            element.text or ""
            for name in package.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            for element in ElementTree.fromstring(package.read(name)).iter(
                "{http://schemas.openxmlformats.org/drawingml/2006/main}t"
            )
        )
    expected = cjk(text)
    if not expected:
        return {"status": "NOT_APPLICABLE", "missing": {}}
    try:
        from pypdf import PdfReader

        actual = cjk(
            "".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages)
        )
    except Exception as exc:
        return {"status": "UNVERIFIED", "error": str(exc), "missing": {}}
    missing = dict(expected - actual)
    return {
        "status": "FAILED" if missing else "TEXT_PRESERVED",
        "missing": missing,
        "claim": "PDF text extraction only; visual glyph inspection remains required",
    }


def _rasterize_pdf(pdf: Path, output_dir: Path) -> List[str]:
    """Rasterize a PDF using an installed command-line rasterizer."""

    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("slide-*.png"):
        stale.unlink()
    prefix = output_dir / "slide"
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        subprocess.run(
            [pdftoppm, "-png", "-r", "144", str(pdf), str(prefix)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    else:
        # ImageMagick is a useful fallback on developer workstations.  The
        # command is still argv-based and never passed through a shell.
        convert = shutil.which("magick") or shutil.which("convert")
        if not convert:
            return []
        subprocess.run(
            [convert, "-density", "144", str(pdf), str(prefix) + "-%d.png"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    return [str(path) for path in sorted(output_dir.glob("slide-*.png"))]


def isolated_font_environment(output_dir):
    """Expose installed macOS fonts to headless Fontconfig without system edits."""
    env = dict(os.environ)
    if platform.system() != "Darwin" or env.get("FONTCONFIG_FILE"):
        return env, {"mode": "inherited", "fontconfig_file": env.get("FONTCONFIG_FILE")}
    root = Path(output_dir).resolve()
    config = ElementTree.Element("fontconfig")
    for directory in (
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path.home() / "Library/Fonts",
    ):
        if directory.is_dir():
            ElementTree.SubElement(config, "dir").text = str(directory)
    cache = root / "font-cache"
    cache.mkdir(parents=True, exist_ok=True)
    ElementTree.SubElement(config, "cachedir").text = str(cache)
    alias = ElementTree.SubElement(config, "alias")
    ElementTree.SubElement(alias, "family").text = "sans-serif"
    prefer = ElementTree.SubElement(alias, "prefer")
    ElementTree.SubElement(prefer, "family").text = "Heiti SC"
    path = root / "fonts.conf"
    ElementTree.ElementTree(config).write(path, encoding="utf-8", xml_declaration=True)
    env["FONTCONFIG_FILE"] = str(path)
    return env, {
        "mode": "isolated_macos_fontconfig",
        "fontconfig_file": str(path),
        "fontconfig_sha256": sha256_file(path),
        "system_fonts_modified": False,
    }


class LibreOfficeBackend(RenderBackend):
    name = "libreoffice"
    acceptance_eligible = False

    def __init__(self, executable: Optional[str] = None):
        self.executable = executable or find_soffice()

    @property
    def available(self) -> bool:
        return bool(
            self.executable
            and (Path(self.executable).exists() or shutil.which(self.executable))
        )

    def render(self, pptx: PathLike, output_dir: PathLike) -> RenderResult:
        invalid = self._invalid_input(pptx, output_dir)
        if invalid:
            return invalid
        if not self.available:
            return self._failure(
                pptx,
                output_dir,
                "LibreOffice is unavailable; install soffice or set PPTRESTORE_SOFFICE.",
            )

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        conversion = Path(tempfile.mkdtemp(prefix="conversion-", dir=str(out)))
        render_env, font_environment = isolated_font_environment(conversion)
        # LO requires a writable, independent user profile.  Keeping this in a
        # TemporaryDirectory also prevents one run's lock files affecting the
        # next run or a developer's normal LO session.
        with tempfile.TemporaryDirectory(
            prefix="pptrestore-lo-profile-"
        ) as profile_dir:
            profile = Path(profile_dir)
            args = [
                self.executable,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(conversion),
                "-env:UserInstallation=" + _file_uri(profile),
                str(Path(pptx).resolve()),
            ]
            try:
                proc = subprocess.run(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    timeout=180,
                    env=render_env,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return self._failure(
                    pptx, output_dir, "LibreOffice render invocation failed: %s" % exc
                )

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "non-zero exit").strip()
            return self._failure(
                pptx, output_dir, "LibreOffice failed: %s" % detail[-1000:]
            )

        pdf = conversion / (Path(pptx).stem + ".pdf")
        try:
            images = _rasterize_pdf(pdf, conversion) if pdf.is_file() else []
        except (OSError, subprocess.SubprocessError) as exc:
            return self._failure(
                pptx, output_dir, "LibreOffice PDF rasterization failed: %s" % exc
            )
        if not images:
            return self._failure(
                pptx,
                output_dir,
                "LibreOffice produced no rasterized slides (pdftoppm/ImageMagick unavailable or conversion failed).",
            )
        version = _renderer_version(self.executable)
        cjk_check = check_pdf_cjk_preservation(pptx, pdf)
        if cjk_check["status"] in {"FAILED", "UNVERIFIED"}:
            return RenderResult(
                backend=self.name,
                success=False,
                output_dir=str(out),
                images=images,
                error="Chinese text preservation failed or is unverified",
                status="FAILED",
                pptx_sha256=sha256_file(pptx),
                renderer_version=version,
                metadata={
                    "cjk_check": cjk_check,
                    "pdf": str(pdf),
                    "font_environment": font_environment,
                },
            )
        return RenderResult(
            backend=self.name,
            success=True,
            output_dir=str(out),
            images=images,
            acceptance_eligible=False,
            status="PREVERIFIED",
            pptx_sha256=sha256_file(pptx),
            renderer_version=version,
            os_info=environment_info(renderer=self.name, renderer_version=version),
            metadata={
                "acceptance": "PREVERIFICATION_ONLY",
                "profile_isolated": True,
                "font_environment": font_environment,
                "cjk_check": cjk_check,
            },
        )


class WpsBackend(RenderBackend):
    """WPS renderer with explicit headless and imported-PDF capability modes.

    Some macOS WPS builds expose presentation PDF export only in the GUI.  In
    that case callers may pass an interactively exported PDF; the backend
    records this provenance and never pretends the GUI is headless.
    """

    name = "wps"
    acceptance_eligible = False

    def __init__(
        self,
        app_path: Optional[str] = None,
        executable: Optional[str] = None,
        exported_pdf: Optional[PathLike] = None,
    ):
        self.app_path = app_path or find_wps()
        self.executable = executable or find_wps_cli(self.app_path)
        self.exported_pdf = (
            str(exported_pdf) if exported_pdf else os.environ.get("PPTRESTORE_WPS_PDF")
        )
        self.headless_available = _wps_supports_ppt2pdf(self.executable)

    @property
    def installed(self) -> bool:
        return bool(self.app_path or self.executable)

    @property
    def available(self) -> bool:
        return self.headless_available or bool(
            self.exported_pdf and Path(self.exported_pdf).is_file()
        )

    def render(self, pptx: PathLike, output_dir: PathLike) -> RenderResult:
        invalid = self._invalid_input(pptx, output_dir)
        if invalid:
            return invalid
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        pdf = out / (Path(pptx).stem + ".pdf")
        mode = "headless_cli"
        if self.exported_pdf:
            source_pdf = Path(self.exported_pdf)
            if not source_pdf.is_file():
                return self._failure(
                    pptx, output_dir, "WPS exported PDF does not exist: %s" % source_pdf
                )
            shutil.copy2(str(source_pdf), str(pdf))
            mode = "imported_pdf"
        elif self.headless_available:
            proc = subprocess.run(
                [
                    str(self.executable),
                    "ppt2pdf",
                    str(Path(pptx).resolve()),
                    "--output",
                    str(pdf),
                    "--json",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=180,
            )
            if proc.returncode != 0 or not pdf.is_file():
                return self._failure(
                    pptx,
                    output_dir,
                    "WPS ppt2pdf failed: %s"
                    % (proc.stderr or proc.stdout or proc.returncode),
                )
        else:
            return self._failure(
                pptx,
                output_dir,
                "WPS is installed but this build has no headless ppt2pdf command; export through WPS and pass --wps-pdf <file>.",
            )
        try:
            images = _rasterize_pdf(pdf, out)
        except (OSError, subprocess.SubprocessError) as exc:
            return self._failure(
                pptx, output_dir, "WPS PDF rasterization failed: %s" % exc
            )
        if not images:
            return self._failure(pptx, output_dir, "WPS produced no rasterized slides.")
        version = read_wps_version(self.app_path)
        metadata = {
            "acceptance": "PREVERIFICATION_ONLY",
            "wps_mode": mode,
            "headless": mode == "headless_cli",
            "imported_pdf": mode == "imported_pdf",
        }
        if self.exported_pdf:
            metadata["exported_pdf_sha256"] = sha256_file(self.exported_pdf)
        if self.app_path:
            metadata["wps_app_path"] = str(self.app_path)
        return RenderResult(
            backend=self.name,
            success=True,
            output_dir=str(out),
            images=images,
            acceptance_eligible=False,
            status="PREVERIFIED",
            pptx_sha256=sha256_file(pptx),
            renderer_version=version,
            os_info=environment_info(renderer=self.name, renderer_version=version),
            metadata=metadata,
        )


class PowerPointBackend(RenderBackend):
    """PowerPoint renderer capability adapter.

    The implementation deliberately reports unavailable when the native host
    is absent.  It never silently substitutes LibreOffice, which is essential
    to the PASS state contract.
    """

    name = "powerpoint"
    acceptance_eligible = True

    def __init__(self):
        self.system = platform.system()
        self._win32 = None
        if self.system == "Windows":
            try:
                import win32com.client  # type: ignore

                self._win32 = win32com.client
            except ImportError:
                self._win32 = None

    @property
    def available(self) -> bool:
        if self.system == "Windows":
            return self._win32 is not None
        if self.system == "Darwin":
            return bool(
                shutil.which("osascript")
                and Path("/Applications/Microsoft PowerPoint.app").exists()
            )
        return False

    def render(self, pptx: PathLike, output_dir: PathLike) -> RenderResult:
        invalid = self._invalid_input(pptx, output_dir)
        if invalid:
            return invalid
        if not self.available:
            detail = (
                "PowerPoint COM automation is unavailable (win32com is not installed)."
                if self.system == "Windows"
                else "Microsoft PowerPoint is unavailable on this execution node; native PowerPoint PASS cannot be produced."
            )
            return self._failure(pptx, output_dir, detail)

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        try:
            if self.system == "Windows":
                images = self._render_windows(Path(pptx), out)
            else:
                images = self._render_macos(Path(pptx), out)
        except Exception as exc:
            return self._failure(pptx, output_dir, "PowerPoint render failed: %s" % exc)
        if not images:
            return self._failure(
                pptx, output_dir, "PowerPoint produced no slide images."
            )
        return RenderResult(
            backend=self.name,
            success=True,
            output_dir=str(out),
            images=images,
            acceptance_eligible=True,
            status="BUILT",
            pptx_sha256=sha256_file(pptx),
            os_info=environment_info(renderer=self.name),
            metadata={"acceptance": "POWERPOINT_FINAL"},
        )

    def _render_windows(self, pptx: Path, output_dir: Path) -> List[str]:
        # Exporting PDF via COM is stable across Office versions.  Rasterizing
        # is shared with the LO backend and remains an argv-based subprocess.
        app = self._win32.Dispatch("PowerPoint.Application")
        app.Visible = False
        presentation = app.Presentations.Open(str(pptx), WithWindow=False)
        pdf = output_dir / (pptx.stem + ".pdf")
        try:
            presentation.ExportAsFixedFormat(str(pdf), 2)  # ppFixedFormatTypePDF
        finally:
            presentation.Close()
            app.Quit()
        return _rasterize_pdf(pdf, output_dir)

    def _render_macos(self, pptx: Path, output_dir: Path) -> List[str]:
        # Keep the AppleScript invocation explicit and parameterized.  The
        # script only exports a PDF; no shell interpolation is involved.
        pdf = output_dir / (pptx.stem + ".pdf")
        script = (
            'tell application "Microsoft PowerPoint" to open POSIX file "{0}"\n'
            'tell application "Microsoft PowerPoint" to save active presentation in POSIX file "{1}" as save as PDF\n'
            'tell application "Microsoft PowerPoint" to close active presentation saving no'
        ).format(str(pptx), str(pdf))
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return _rasterize_pdf(pdf, output_dir)


class AutoRenderBackend(RenderBackend):
    """Choose PowerPoint, WPS, then LibreOffice by capability."""

    name = "auto"

    def __init__(
        self,
        backends: Optional[Sequence[RenderBackend]] = None,
        wps_pdf: Optional[PathLike] = None,
    ):
        self.backends = (
            list(backends)
            if backends is not None
            else [
                PowerPointBackend(),
                WpsBackend(exported_pdf=wps_pdf),
                LibreOfficeBackend(),
            ]
        )
        self.selected_backend: Optional[RenderBackend] = None

    @property
    def available(self) -> bool:
        return any(backend.available for backend in self.backends)

    def render(self, pptx: PathLike, output_dir: PathLike) -> RenderResult:
        for backend in self.backends:
            if not backend.available:
                continue
            result = backend.render(pptx, output_dir)
            self.selected_backend = backend
            if result.success:
                result.metadata.setdefault("selection", "auto")
                return result
        # Return the most informative unavailable result, preferring the native
        # backend so callers understand why PASS is impossible.
        self.selected_backend = self.backends[0] if self.backends else None
        if self.selected_backend:
            return self.selected_backend.render(pptx, output_dir)
        return RenderResult(
            backend=self.name,
            success=False,
            status="FAILED",
            error="No render backend configured",
        )
