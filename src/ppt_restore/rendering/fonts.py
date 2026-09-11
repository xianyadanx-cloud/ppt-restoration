"""Cross-platform font discovery and deterministic font metadata.

FontTools is a base package dependency.  Imports remain guarded so ``doctor``
can still produce an actionable capability report in an incomplete runtime.
"""

from __future__ import annotations

import hashlib
import os
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

try:  # optional dependency
    from fontTools.ttLib import TTCollection, TTFont  # type: ignore
except Exception:  # pragma: no cover - exercised on minimal installs
    TTFont = None
    TTCollection = None


@dataclass(frozen=True)
class FontInfo:
    family: str
    path: str
    sha256: str
    font_number: int = 0
    style: str = "regular"
    weight: int = 400
    italic: bool = False
    glyph_count: int = 0
    units_per_em: int = 1000
    coverage: Tuple[int, ...] = ()
    readable: bool = True
    metadata_available: bool = False

    def supports(self, text: str) -> bool:
        return (
            all(ord(ch) in set(self.coverage) for ch in str(text))
            if self.coverage
            else False
        )

    def to_dict(self):
        d = asdict(self)
        d["coverage"] = list(self.coverage)
        return d


def _platform_font_dirs() -> List[Path]:
    home = Path.home()
    system = platform.system().lower()
    if system == "windows":
        candidates = [
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
            home / "AppData/Local/Microsoft/Windows/Fonts",
        ]
    elif system == "darwin":
        candidates = [
            Path("/System/Library/Fonts"),
            Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8"),
            Path("/Library/Fonts"),
            home / "Library/Fonts",
        ]
    else:
        candidates = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            home / ".fonts",
            home / ".local/share/fonts",
        ]
    return list(dict.fromkeys(candidates))


class FontRegistry:
    """A deterministic, hash-addressed font registry."""

    EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}

    def __init__(
        self,
        search_dirs: Optional[Sequence[os.PathLike]] = None,
        auto_scan: bool = True,
    ):
        self.search_dirs = [
            Path(p).expanduser()
            for p in (search_dirs if search_dirs is not None else _platform_font_dirs())
        ]
        self.fonts: List[FontInfo] = []
        self._by_family: Dict[str, List[FontInfo]] = {}
        if auto_scan:
            self.scan()

    @property
    def entries(self) -> Tuple[FontInfo, ...]:
        return tuple(self.fonts)

    def clear(self) -> None:
        self.fonts.clear()
        self._by_family.clear()

    def scan(
        self, search_dirs: Optional[Sequence[os.PathLike]] = None
    ) -> List[FontInfo]:
        if search_dirs is not None:
            self.search_dirs = [Path(p).expanduser() for p in search_dirs]
        seen: Set[Tuple[str, int]] = {(f.path, f.font_number) for f in self.fonts}
        paths: List[Path] = []
        for root in self.search_dirs:
            if not root.exists() or not root.is_dir():
                continue
            try:
                paths.extend(
                    p
                    for p in root.rglob("*")
                    if p.is_file() and p.suffix.lower() in self.EXTENSIONS
                )
            except OSError:
                continue
        for path in sorted(set(paths), key=lambda p: str(p).lower()):
            if any(item[0] == str(path) for item in seen):
                continue
            for info in self._inspect_all(path):
                self.register(info)
                seen.add((str(path), info.font_number))
        return list(self.fonts)

    def register(self, info_or_path, **kwargs) -> FontInfo:
        if isinstance(info_or_path, FontInfo):
            info = info_or_path
        else:
            info = self._inspect(Path(info_or_path), **kwargs)
            if info is None:
                raise ValueError("not a readable font: %s" % info_or_path)
        if (info.path, info.font_number) not in {
            (f.path, f.font_number) for f in self.fonts
        }:
            self.fonts.append(info)
            self._by_family.setdefault(info.family.casefold(), []).append(info)
        return info

    def find(
        self,
        family: str,
        text: Optional[str] = None,
        weight: Optional[int] = None,
        italic: Optional[bool] = None,
    ) -> Optional[FontInfo]:
        candidates = self._by_family.get(str(family).casefold(), [])
        if not candidates:
            candidates = [
                f for f in self.fonts if str(family).casefold() in f.family.casefold()
            ]
        if text is not None:
            # A requested family that cannot render the text is not a match.
            # Returning it here would silently delegate glyph substitution to
            # Office and make line wrapping environment-dependent.
            candidates = [f for f in candidates if f.supports(text)]
        if weight is not None:
            candidates = sorted(candidates, key=lambda f: abs(f.weight - int(weight)))
        if italic is not None:
            candidates = sorted(candidates, key=lambda f: int(f.italic != italic))
        return candidates[0] if candidates else None

    resolve = find

    def find_fallback(
        self,
        text: str,
        preferred: Sequence[str] = (
            "Noto Sans CJK SC",
            "Source Han Sans SC",
            "Microsoft YaHei",
            "PingFang SC",
            "Hiragino Sans GB",
            "Arial Unicode MS",
            "Arial Unicode",
            "DejaVu Sans",
            "Liberation Sans",
        ),
    ) -> Optional[FontInfo]:
        for family in preferred:
            found = self.find(family, text=text)
            if found:
                return found
        return next((f for f in self.fonts if f.supports(text)), None)

    def measure_text_width_pt(
        self, text: str, family: str, font_size_pt: float, weight: Optional[int] = None
    ) -> float:
        """Measure advance width from the selected font's real hmtx table.

        This deliberately fails when the family or glyph coverage is missing;
        callers may then emit an explicit fallback report instead of silently
        using a heuristic or a renderer-selected substitute.
        """
        info = self.find(family, text=text, weight=weight)
        if info is None:
            raise LookupError("font does not cover text: %s" % family)
        if TTFont is None:
            raise RuntimeError(
                "fontTools is required for deterministic text measurement"
            )
        font = TTFont(info.path, lazy=True, fontNumber=info.font_number)
        try:
            cmap = font.getBestCmap() or {}
            metrics = font["hmtx"].metrics
            units_per_em = float(font["head"].unitsPerEm)
            total = 0
            for char in str(text):
                glyph = cmap.get(ord(char))
                if glyph is None or glyph not in metrics:
                    raise LookupError("font %s is missing U+%04X" % (family, ord(char)))
                total += metrics[glyph][0]
            return float(total) * float(font_size_pt) / units_per_em
        finally:
            font.close()

    def coverage(self, family: str) -> Set[int]:
        info = self.find(family)
        return set(info.coverage) if info else set()

    def rank_candidates(
        self,
        text: str,
        font_size_pt: float,
        target_width_pt: float,
        weight: int = 400,
        limit: int = 5,
    ):
        """Rank installed families by advance-width error, not font identity.

        A low error is a measurement aid only: unrelated faces may have the
        same advances and need direct visual comparison.
        """
        if font_size_pt <= 0 or target_width_pt <= 0:
            raise ValueError("font size and target width must be positive")
        results = []
        for family in sorted({f.family for f in self.entries}):
            info = self.find(family, text=text, weight=weight)
            if info is None:
                continue
            try:
                width = self.measure_text_width_pt(text, family, font_size_pt, weight)
            except (LookupError, RuntimeError, OSError, ValueError):
                continue
            results.append(
                {
                    "family": family,
                    "font_sha256": info.sha256,
                    "font_number": info.font_number,
                    "weight": info.weight,
                    "advance_width_pt": width,
                    "width_error_pt": abs(width - target_width_pt),
                    "recognition_status": "UNCONFIRMED",
                }
            )
        return sorted(
            results, key=lambda item: (item["width_error_pt"], item["family"])
        )[: max(1, limit)]

    def report(self) -> Dict[str, object]:
        return {
            "count": len(self.fonts),
            "fonttools": TTFont is not None,
            "search_dirs": [str(p) for p in self.search_dirs],
            "fonts": [f.to_dict() for f in self.fonts],
        }

    def _inspect_all(self, path: Path) -> List[FontInfo]:
        count = 1
        if path.suffix.lower() in {".ttc", ".otc"} and TTCollection is not None:
            try:
                collection = TTCollection(str(path), lazy=True)
                count = len(collection.fonts)
                collection.close()
            except Exception:
                count = 1
        return [
            info
            for index in range(count)
            if (info := self._inspect(path, font_number=index)) is not None
        ]

    def _inspect(self, path: Path, **kwargs) -> Optional[FontInfo]:
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, ValueError):
            return None
        family = path.stem
        style = "regular"
        weight = 400
        italic = False
        coverage: Set[int] = set()
        glyph_count = 0
        upem = 1000
        metadata = False
        if TTFont is not None:
            try:
                font = TTFont(
                    str(path), lazy=True, fontNumber=int(kwargs.get("font_number", 0))
                )
                metadata = True
                names = font["name"].names
                decoded = []
                for n in names:
                    if n.nameID in (1, 16):
                        try:
                            decoded.append(n.toUnicode())
                        except Exception:
                            pass
                if decoded:
                    family = next((x for x in decoded if x), family)
                if "head" in font:
                    upem = int(font["head"].unitsPerEm)
                if "maxp" in font:
                    glyph_count = int(font["maxp"].numGlyphs)
                if "OS/2" in font:
                    weight = int(getattr(font["OS/2"], "usWeightClass", 400))
                if "post" in font:
                    italic = bool(getattr(font["post"], "italicAngle", 0))
                if "cmap" in font:
                    for table in font["cmap"].tables:
                        coverage.update(table.cmap.keys())
                lower = path.stem.casefold()
                italic = italic or "italic" in lower or "oblique" in lower
                if "bold" in lower:
                    weight = max(weight, 700)
                font.close()
            except Exception:
                metadata = False
        return FontInfo(
            family=family,
            path=str(path),
            sha256=digest,
            font_number=int(kwargs.get("font_number", 0)),
            style=style,
            weight=weight,
            italic=italic,
            glyph_count=glyph_count,
            units_per_em=upem,
            coverage=tuple(sorted(coverage)),
            metadata_available=metadata,
        )


__all__ = ["FontInfo", "FontRegistry"]
