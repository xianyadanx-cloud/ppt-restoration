"""Deterministic visual evidence extraction for the host multimodal Agent.

Evidence is intentionally not a SceneSpec.  Connected components and
projection bands are candidates the Agent may use, never instructions to
compile hundreds of glyph fragments as PPT shapes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

from ppt_restore.contracts.schema_v2 import EvidenceBundle
from ppt_restore.platform.analyze import (
    _edge_components,
    _sample_color,
    _semantic_regions,
    dominant_colors,
)
from ppt_restore.platform.io import write_json
from ppt_restore.platform.ocr import (
    OcrProvider,
    TextDetection,
    auto_ocr_providers,
    run_ocr,
)
from ppt_restore.platform.provenance import sha256_file

PathLike = Union[str, Path]


def _primitive_type(
    box: Tuple[float, float, float, float], canvas: Tuple[int, int]
) -> str:
    _, _, width, height = box
    page_width, page_height = canvas
    if width >= page_width * 0.25 and width >= max(1.0, height) * 8:
        return "horizontal_line"
    if height >= page_height * 0.25 and height >= max(1.0, width) * 8:
        return "vertical_line"
    if 0.30 <= width / max(1.0, height) <= 3.5:
        return "candidate_rectangle"
    return "raw_component"


def _ocr_row(index: int, detection: TextDetection) -> Dict[str, Any]:
    return {
        "id": "ocr-%04d" % index,
        "text": detection.text,
        "bbox_px": [float(value) for value in detection.bbox_px],
        "confidence": float(detection.confidence),
        "provider": detection.provider,
    }


def extract_evidence(
    image_path: PathLike,
    *,
    ocr_provider: Optional[OcrProvider] = None,
    ocr_mode: str = "auto",
    output_path: Optional[PathLike] = None,
) -> EvidenceBundle:
    """Extract an EvidenceBundle from a canonical image."""

    source = Path(image_path)
    if not source.is_file():
        raise FileNotFoundError(str(source))
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    width, height = image.size

    disabled = ocr_provider is False
    warnings: List[str] = []
    attempts: List[Dict[str, Any]] = []
    selected_provider = None
    if ocr_mode not in ("auto", "none"):
        raise ValueError("unsupported ocr_mode: %s" % ocr_mode)

    # ``ocr_provider`` remains injectable for deterministic tests and for
    # explicit adapters.  A sequence is treated as an explicit cascade,
    # which is useful for embedding applications that have their own provider
    # discovery.  Auto mode always constructs the complete local chain rather
    # than selecting one provider up front.
    if disabled or ocr_mode == "none":
        providers: List[OcrProvider] = []
    elif ocr_provider is None:
        providers = list(auto_ocr_providers())
    elif isinstance(ocr_provider, (list, tuple)):
        providers = list(ocr_provider)
    else:
        providers = [ocr_provider]

    detections: List[TextDetection] = []
    if disabled:
        warnings.append("OCR provider unavailable")
        ocr_status = "unavailable"
    elif ocr_mode == "none":
        ocr_status = "disabled"
    elif providers:
        detections, attempts, provider_warnings, selected_provider, ocr_status = (
            run_ocr(image, providers)
        )
        warnings.extend(provider_warnings)
        if not detections and ocr_status == "zero_detections":
            warnings.append(
                "OCR completed with zero detections; critical text requires manual or model review"
            )
        elif (
            not detections
            and ocr_status in ("failed", "unavailable")
            and "OCR provider unavailable" not in warnings
        ):
            warnings.append(
                "OCR provider unavailable"
                if ocr_status == "unavailable"
                else "OCR cascade produced no detections"
            )
    else:
        ocr_status = "unavailable"
        warnings.append("OCR provider unavailable")

    components = _edge_components(image)
    primitives: List[Dict[str, Any]] = []
    for index, component in enumerate(components[:512], 1):
        x, y, w, h, pixels = component
        bbox = (float(x), float(y), float(w), float(h))
        primitives.append(
            {
                "id": "primitive-%04d" % index,
                "type": _primitive_type(bbox, (width, height)),
                "bbox_px": list(bbox),
                "pixel_count": int(pixels),
                "sample_color": "#%02X%02X%02X" % _sample_color(image, bbox),
                "source_method": "pillow.edge_components",
            }
        )

    regions: List[Dict[str, Any]] = []
    semantic = _semantic_regions(image)
    if semantic:
        for index, (name, box) in enumerate(semantic, 1):
            regions.append(
                {
                    "id": "region-%02d" % index,
                    "kind": "layout_candidate",
                    "label": name,
                    "bbox_px": [float(value) for value in box],
                    "confidence": 0.60,
                    "source_method": "pillow.projection",
                }
            )

    guides = []
    for primitive in primitives:
        if primitive["type"] in ("horizontal_line", "vertical_line"):
            guides.append(
                {
                    "id": primitive["id"],
                    "orientation": "horizontal"
                    if primitive["type"] == "horizontal_line"
                    else "vertical",
                    "bbox_px": primitive["bbox_px"],
                    "confidence": 0.80,
                }
            )

    # ``zero_detections`` and all failure states are intentionally explicit.
    # The host Agent can still inspect canonical.png, but must not treat an
    # empty OCR list as proof that the slide contains no text.
    metadata = {
        "warning": warnings,
        "ocr_status": ocr_status,
        "ocr_provider": selected_provider,
        "ocr_attempts": attempts,
        "ocr_line_count": len(detections),
        "ocr_zero_detections": not bool(detections),
        "ocr_degraded": ocr_status != "completed",
        "ocr_requires_manual_review": not bool(detections),
        "ocr_requested_mode": ocr_mode,
        "raw_component_count": len(components),
        "algorithm_version": "evidence-1",
    }
    bundle = EvidenceBundle(
        schema_version="1.0",
        canonical_sha256=sha256_file(source),
        canvas={
            "width_px": width,
            "height_px": height,
            "color_space": "sRGB",
            "dpi": 96.0,
        },
        ocr_lines=tuple(
            _ocr_row(index, detection) for index, detection in enumerate(detections, 1)
        ),
        visual_primitives=tuple(primitives),
        palette=tuple(dominant_colors(image)),
        guides=tuple(guides),
        regions=tuple(regions),
        # Keep the evidence hash portable when a case directory is copied to
        # another machine.  Absolute paths belong in agent_request.json, not
        # in content-addressed semantic evidence.
        artifacts=tuple(
            (
                {
                    "kind": "canonical",
                    "path": "canonical.png",
                    "sha256": sha256_file(source),
                },
            )
        ),
        producer=metadata,
    )
    if output_path is not None:
        write_json(output_path, bundle)
    return bundle


def read_evidence(path: PathLike) -> EvidenceBundle:
    source = Path(path)
    return EvidenceBundle.from_json(source.read_text(encoding="utf-8"))


__all__ = ["extract_evidence", "read_evidence"]
