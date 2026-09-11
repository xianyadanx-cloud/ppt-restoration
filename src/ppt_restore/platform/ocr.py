"""Optional OCR adapters; Scene geometry never depends on an LLM."""

from __future__ import annotations

import abc
import csv
import io
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PIL import Image


@dataclass(frozen=True)
class TextDetection:
    text: str
    bbox_px: Tuple[float, float, float, float]
    confidence: float
    provider: str

    def to_dict(self):
        return asdict(self)


class OcrProvider(abc.ABC):
    name = "unknown"

    @property
    def available(self) -> bool:
        return True

    @abc.abstractmethod
    def recognize(self, image, regions=None) -> List[TextDetection]:
        raise NotImplementedError


class ImportedTextProvider(OcrProvider):
    """Explicit user-supplied text; never presents imported text as OCR."""

    name = "imported_text"

    def __init__(self, detections: Iterable[TextDetection]):
        self.detections = list(detections)

    def recognize(self, image, regions=None) -> List[TextDetection]:
        return list(self.detections)


class TesseractOcrProvider(OcrProvider):
    name = "tesseract"

    def __init__(self, executable: Optional[str] = None, language: str = "eng"):
        self.executable = executable or shutil.which("tesseract")
        self.language = language

    @property
    def available(self) -> bool:
        return bool(self.executable)

    def recognize(self, image, regions=None) -> List[TextDetection]:
        if not self.available:
            raise RuntimeError("Tesseract OCR is unavailable")
        opened = (
            image.copy()
            if isinstance(image, Image.Image)
            else Image.open(image).convert("RGB")
        )
        boxes = list(regions or [(0, 0, opened.width, opened.height)])
        detections: List[TextDetection] = []
        with tempfile.TemporaryDirectory(prefix="pptrestore-ocr-") as directory:
            for index, region in enumerate(boxes):
                left, top, width, height = [int(round(value)) for value in region]
                crop = opened.crop((left, top, left + width, top + height))
                source = Path(directory) / ("region-%d.png" % index)
                crop.save(source)
                proc = subprocess.run(
                    [
                        str(self.executable),
                        str(source),
                        "stdout",
                        "-l",
                        self.language,
                        "tsv",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    timeout=120,
                )
                if proc.returncode != 0:
                    raise RuntimeError(
                        "Tesseract failed: %s"
                        % (proc.stderr or "unknown error").strip()
                    )
                for row in csv.DictReader(io.StringIO(proc.stdout), delimiter="\t"):
                    text = (row.get("text") or "").strip()
                    try:
                        confidence = float(row.get("conf", "-1")) / 100.0
                    except ValueError:
                        confidence = -1.0
                    if not text or confidence < 0:
                        continue
                    x, y = left + int(row["left"]), top + int(row["top"])
                    detections.append(
                        TextDetection(
                            text,
                            (x, y, int(row["width"]), int(row["height"])),
                            min(1.0, confidence),
                            self.name,
                        )
                    )
        return detections


class MacVisionOcrProvider(OcrProvider):
    """Use the repository's native macOS Vision OCR adapter when available."""

    name = "mac_vision"

    def __init__(self, script: Optional[str] = None, swift: Optional[str] = None):
        self.script = script or str(
            files("ppt_restore").joinpath("resources", "mac_vision_ocr.swift")
        )
        self.swift = swift or shutil.which("swift")

    @property
    def available(self) -> bool:
        return bool(self.swift and Path(self.script).is_file())

    def recognize(self, image, regions=None) -> List[TextDetection]:
        if not self.available:
            raise RuntimeError("macOS Vision OCR is unavailable")
        if isinstance(image, Image.Image):
            with tempfile.TemporaryDirectory(prefix="pptrestore-vision-") as directory:
                source = Path(directory) / "source.png"
                image.convert("RGB").save(source)
                return self._recognize_path(source, image.size)
        source = Path(image)
        with Image.open(source) as opened:
            size = opened.size
        return self._recognize_path(source, size)

    def _recognize_path(
        self, source: Path, size: Tuple[int, int]
    ) -> List[TextDetection]:
        proc = subprocess.run(
            [str(self.swift), self.script, str(source)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "Vision OCR failed: %s" % (proc.stderr or "unknown error").strip()
            )
        try:
            rows = json.loads(proc.stdout or "[]")
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Vision OCR returned invalid JSON: %s" % exc)
        width, height = size
        detections = []
        for row in rows if isinstance(rows, list) else []:
            text = str(row.get("text", "")).strip()
            box = row.get("box_px")
            if not box:
                norm = row.get("box_norm")
                if isinstance(norm, (list, tuple)) and len(norm) == 4:
                    box = [
                        float(norm[0]) * width / 1000.0,
                        float(norm[1]) * height / 1000.0,
                        float(norm[2]) * width / 1000.0,
                        float(norm[3]) * height / 1000.0,
                    ]
            if not text or not isinstance(box, (list, tuple)) or len(box) != 4:
                continue
            detections.append(
                TextDetection(
                    text,
                    tuple(float(x) for x in box),
                    min(1.0, max(0.0, float(row.get("confidence", 0.0)))),
                    self.name,
                )
            )
        return detections


def auto_ocr_provider(language: str = "chi_sim+eng") -> Optional[OcrProvider]:
    """Return the first *discoverable* provider for backwards compatibility.

    Historically callers used this helper as a selector and then invoked the
    returned provider directly.  Keep that API stable, but do not use it for
    the default evidence path: a provider can advertise ``available`` and
    still fail at execution time (for example when the Swift/SDK pair is
    incompatible).  :func:`auto_ocr_providers` and :func:`run_ocr` provide the
    runtime cascade used by the v2 pipeline.
    """
    for provider in auto_ocr_providers(language=language):
        try:
            if provider.available:
                return provider
        except Exception:
            # Availability probes are best-effort.  The cascade records a
            # structured failure when it actually tries the provider.
            continue
    return None


def auto_ocr_providers(language: str = "chi_sim+eng") -> List[OcrProvider]:
    """Build the deterministic local OCR provider chain.

    Vision is attempted first, followed by Tesseract with the requested
    language and (when applicable) an English-only retry.  The chain includes
    unavailable providers as well as available ones so evidence can explain
    exactly why OCR was or was not produced.  It deliberately does not run
    anything; execution and failure capture belong to :func:`run_ocr`.
    """
    providers: List[OcrProvider] = [
        MacVisionOcrProvider(),
        TesseractOcrProvider(language=language),
    ]
    if language != "eng":
        providers.append(TesseractOcrProvider(language="eng"))
    return providers


def _provider_name(provider: OcrProvider) -> str:
    """Return a stable human-readable provider name for evidence records."""

    value = getattr(provider, "name", None)
    if value:
        return str(value)
    return provider.__class__.__name__.lower()


def _provider_label(provider: OcrProvider) -> str:
    """Include useful configuration without changing detection provider IDs."""

    name = _provider_name(provider)
    language = getattr(provider, "language", None)
    return "%s[%s]" % (name, language) if language else name


def _error_detail(exc: Exception, limit: int = 4000) -> str:
    """Keep provider diagnostics useful without bloating Agent handoff JSON."""

    detail = "%s: %s" % (exc.__class__.__name__, str(exc).strip() or "unknown error")
    if len(detail) <= limit:
        return detail
    head = max(1, (limit - 40) // 2)
    tail = max(1, limit - 40 - head)
    return detail[:head] + " ... [truncated] ... " + detail[-tail:]


def run_ocr(
    image,
    providers: Iterable[OcrProvider],
    *,
    stop_on_detections: bool = True,
) -> Tuple[List[TextDetection], List[dict], List[str], Optional[str], str]:
    """Run OCR providers as a failure-tolerant cascade.

    Returns ``(detections, attempts, warnings, selected_provider, status)``.
    Each attempt is JSON-safe and contains availability, execution status,
    detection count, and an error when applicable.  Empty successful results
    are recorded as ``zero_detections`` and do not prevent a later provider
    from trying.  Provider exceptions are captured and the chain continues.

    ``stop_on_detections`` is exposed for deterministic tests and future
    callers that want to combine multiple successful providers.  The default
    preserves the cascade semantics: the first provider with detections wins.
    """

    detections: List[TextDetection] = []
    attempts: List[dict] = []
    warnings: List[str] = []
    selected_provider: Optional[str] = None
    saw_available = False
    saw_success = False

    for index, provider in enumerate(providers, 1):
        name = _provider_name(provider)
        label = _provider_label(provider)
        attempt = {
            "index": index,
            "provider": name,
            "label": label,
            "available": False,
            "status": "not_attempted",
            "detections": 0,
            "error": None,
        }
        try:
            available = bool(provider.available)
        except Exception as exc:  # availability probes must not abort the chain
            detail = _error_detail(exc)
            attempt.update({"status": "availability_failed", "error": detail})
            warnings.append(
                "OCR provider %s availability check failed: %s" % (label, detail)
            )
            attempts.append(attempt)
            continue
        attempt["available"] = available
        if not available:
            attempt.update(
                {"status": "unavailable", "error": "%s is unavailable" % label}
            )
            attempts.append(attempt)
            continue

        saw_available = True
        try:
            result = list(provider.recognize(image) or [])
            # A provider must return TextDetection-like values.  Preserve the
            # existing concrete type while rejecting malformed adapters as a
            # provider failure that can fall through to the next adapter.
            for detection in result:
                if not isinstance(detection, TextDetection):
                    raise TypeError("provider returned a non-TextDetection value")
            count = len(result)
            attempt["detections"] = count
            attempt["status"] = "completed" if count else "zero_detections"
            attempts.append(attempt)
            saw_success = True
            if count:
                detections.extend(result)
                selected_provider = name
                if stop_on_detections:
                    break
        except Exception as exc:  # provider-specific failures are evidence
            detail = _error_detail(exc)
            attempt.update({"status": "failed", "error": detail})
            attempts.append(attempt)
            warnings.append("OCR provider %s failed: %s" % (label, detail))

    if detections:
        status = "completed"
    elif saw_success:
        # At least one provider ran successfully but all returned no text.
        status = "zero_detections"
    elif saw_available or attempts:
        # A provider was discovered but failed during execution, or all
        # discovered providers explicitly reported unavailable.
        status = "failed" if saw_available else "unavailable"
    else:
        status = "unavailable"
    return detections, attempts, warnings, selected_provider, status


__all__ = [
    "ImportedTextProvider",
    "OcrProvider",
    "TextDetection",
    "TesseractOcrProvider",
    "MacVisionOcrProvider",
    "auto_ocr_provider",
    "auto_ocr_providers",
    "run_ocr",
]
