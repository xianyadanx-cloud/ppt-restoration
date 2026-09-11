"""Quality state machine and native PPTX acceptance gate."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from ppt_restore.quality.metrics import MetricEngine, MetricReport


class QualityStatus(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    ANALYZED = "ANALYZED"
    BUILT = "BUILT"
    PREVERIFIED = "PREVERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class QualityGateConfig:
    """Versioned thresholds; pages may not lower these ad hoc."""

    version: str = "1.0"
    min_ssim: float = 0.92
    max_explicit_error_rate: float = 0.05
    min_edge_f1: float = 0.80
    min_bbox_iou: float = 0.95
    max_center_error_px: float = 2.0
    max_color_delta: float = 3.0
    max_color_delta_p95: float = 8.0
    min_confidence: float = 0.70
    min_registration_confidence: float = 0.90
    # Legacy cases remain strict by default.  v2 may explicitly opt into the
    # hybrid strategy, where decorative raster nodes are permitted while all
    # critical semantic content stays editable/native.
    strict_native: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "min_ssim": self.min_ssim,
            "max_explicit_error_rate": self.max_explicit_error_rate,
            "min_edge_f1": self.min_edge_f1,
            "min_bbox_iou": self.min_bbox_iou,
            "max_center_error_px": self.max_center_error_px,
            "max_color_delta": self.max_color_delta,
            "max_color_delta_p95": self.max_color_delta_p95,
            "min_confidence": self.min_confidence,
            "min_registration_confidence": self.min_registration_confidence,
            "strict_native": self.strict_native,
        }


@dataclass
class GateDecision:
    status: QualityStatus
    passed: bool = False
    reasons: List[str] = field(default_factory=list)
    picture_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    renderer: Optional[str] = None
    threshold_version: str = "1.0"
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        if key == "status":
            return self.status.value
        if key == "passed":
            return self.passed
        return getattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "passed": self.passed,
            "reasons": list(self.reasons),
            "picture_count": self.picture_count,
            "metrics": dict(self.metrics),
            "renderer": self.renderer,
            "threshold_version": self.threshold_version,
            "provenance": dict(self.provenance),
        }


def inspect_picture_count(pptx_path: Union[os.PathLike, str]) -> Dict[str, Any]:
    """Count ``p:pic`` elements without loading or rewriting the PPTX."""

    path = Path(pptx_path)
    if not path.is_file():
        return {
            "picture_count": -1,
            "status": QualityStatus.INVALID_INPUT.value,
            "error": "PPTX not found",
        }
    count = 0
    shapes = 0
    tables = 0
    textboxes = 0
    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = [
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ]
            for name in names:
                root = ET.fromstring(archive.read(name))
                for element in root.iter():
                    tag = element.tag.rsplit("}", 1)[-1]
                    if tag == "pic":
                        count += 1
                    elif tag == "sp":
                        shapes += 1
                    elif tag == "tbl":
                        tables += 1
                    elif tag == "txBody":
                        textboxes += 1
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        return {
            "picture_count": -1,
            "status": QualityStatus.FAIL.value,
            "error": str(exc),
        }
    return {
        "picture_count": count,
        "shape_count": shapes,
        "table_count": tables,
        "textbox_count": textboxes,
        "is_pure_vector": count == 0,
        "status": "PASS" if count == 0 else QualityStatus.FAIL.value,
    }


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _metric_values(report: Any) -> Dict[str, Any]:
    if isinstance(report, MetricReport):
        return dict(report.metrics)
    if isinstance(report, Mapping):
        metrics = report.get("metrics")
        if isinstance(metrics, Mapping):
            return dict(metrics)
        return dict(report)
    return {}


def _metric_passes(metrics: Mapping[str, Any], config: QualityGateConfig) -> bool:
    color = metrics.get("color_delta", metrics.get("color_delta_ciede2000", 0.0))
    if isinstance(color, Mapping):
        color = color.get("mean", float("inf"))
    checks = (
        ("ssim", metrics.get("ssim", 0.0) >= config.min_ssim),
        (
            "explicit_error_rate",
            metrics.get("explicit_error_rate", 1.0) < config.max_explicit_error_rate,
        ),
        ("edge_f1", metrics.get("edge_f1", 0.0) >= config.min_edge_f1),
        ("color_delta", float(color) <= config.max_color_delta),
        (
            "color_delta_p95",
            float(metrics.get("color_delta_p95", 0.0)) <= config.max_color_delta_p95,
        ),
    )
    if "bbox_iou" in metrics:
        checks += (("bbox_iou", metrics["bbox_iou"] >= config.min_bbox_iou),)
    if "center_error_px" in metrics:
        checks += (
            (
                "center_error_px",
                metrics["center_error_px"] <= config.max_center_error_px,
            ),
        )
    return all(ok for _, ok in checks)


def _low_confidence(scene: Any, threshold: float) -> List[str]:
    if scene is None:
        return []
    found: List[str] = []

    def visit(value: Any, path: str = "scene") -> None:
        if isinstance(value, Mapping):
            confidence = value.get("confidence")
            if isinstance(confidence, Mapping):
                confidence = confidence.get("score", confidence.get("value"))
            if isinstance(confidence, (float, int)) and confidence < threshold:
                found.append(
                    "%s confidence %.3f below %.3f" % (path, confidence, threshold)
                )
            for key, child in value.items():
                if key not in ("evidence", "provenance"):
                    visit(child, path + "." + str(key))
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, "%s[%d]" % (path, index))
        elif is_dataclass(value):
            confidence = getattr(value, "confidence", None)
            if isinstance(confidence, Mapping):
                confidence = confidence.get("score", confidence.get("value"))
            if isinstance(confidence, (float, int)) and confidence < threshold:
                found.append(
                    "%s confidence %.3f below %.3f" % (path, confidence, threshold)
                )
            for item in fields(value):
                if item.name not in ("evidence", "provenance"):
                    visit(getattr(value, item.name), path + "." + item.name)
        else:
            confidence = getattr(value, "confidence", None)
            if isinstance(confidence, Mapping):
                confidence = confidence.get("score", confidence.get("value"))
            if isinstance(confidence, (float, int)) and confidence < threshold:
                found.append(
                    "%s confidence %.3f below %.3f" % (path, confidence, threshold)
                )

    visit(scene)
    return found


class GateEngine:
    """Apply all acceptance rules and emit one of the seven allowed states."""

    ALLOWED_STATUSES = frozenset(item.value for item in QualityStatus)

    def __init__(
        self,
        config: Optional[QualityGateConfig] = None,
        metric_engine: Optional[MetricEngine] = None,
    ):
        self.config = config or QualityGateConfig()
        self.metric_engine = metric_engine or MetricEngine(
            {
                "version": self.config.version,
                "ssim": self.config.min_ssim,
                "explicit_error_rate": self.config.max_explicit_error_rate,
                "edge_f1": self.config.min_edge_f1,
                "bbox_iou": self.config.min_bbox_iou,
                "center_error_px": self.config.max_center_error_px,
                "color_delta": self.config.max_color_delta,
                "color_delta_p95": self.config.max_color_delta_p95,
            }
        )

    def evaluate(
        self,
        scene: Any = None,
        metric_report: Any = None,
        render_result: Any = None,
        *,
        pptx_path: Optional[Union[os.PathLike, str]] = None,
        input_path: Optional[Union[os.PathLike, str]] = None,
        stage: Optional[str] = None,
        registration: Any = None,
        provenance: Optional[Mapping[str, Any]] = None,
    ) -> GateDecision:
        reasons: List[str] = []
        if input_path is not None and not Path(input_path).is_file():
            return GateDecision(
                QualityStatus.INVALID_INPUT,
                reasons=["missing input: %s" % input_path],
                threshold_version=self.config.version,
            )
        if pptx_path is not None and not Path(pptx_path).is_file():
            return GateDecision(
                QualityStatus.INVALID_INPUT,
                reasons=["missing PPTX: %s" % pptx_path],
                threshold_version=self.config.version,
            )
        if render_result is None:
            return GateDecision(
                QualityStatus.FAIL,
                reasons=["render result is required"],
                threshold_version=self.config.version,
            )
        if registration is not None:
            registration_confidence = _value(registration, "confidence", 0.0)
            if (
                not isinstance(registration_confidence, (int, float))
                or registration_confidence < self.config.min_registration_confidence
            ):
                return GateDecision(
                    QualityStatus.NEEDS_REVIEW,
                    reasons=[
                        "registration confidence below %.2f"
                        % self.config.min_registration_confidence
                    ],
                    threshold_version=self.config.version,
                    provenance=dict(provenance or {}),
                )

        render_success = bool(_value(render_result, "success", False))
        renderer = _value(render_result, "backend", None) or _value(
            render_result, "renderer", None
        )
        if not render_success:
            message = _value(render_result, "error", None) or "render failed"
            return GateDecision(
                QualityStatus.FAIL,
                reasons=[str(message)],
                renderer=renderer,
                threshold_version=self.config.version,
            )

        dom = {"picture_count": 0, "status": "PASS"}
        if pptx_path is not None:
            dom = inspect_picture_count(pptx_path)
            if dom.get("picture_count", -1) < 0:
                return GateDecision(
                    QualityStatus.FAIL,
                    reasons=["unable to inspect PPTX DOM"],
                    renderer=renderer,
                    threshold_version=self.config.version,
                )
            if self.config.strict_native and dom.get("picture_count", 0) != 0:
                return GateDecision(
                    QualityStatus.FAIL,
                    reasons=[
                        "PICTURE count must be 0; found %d" % dom["picture_count"]
                    ],
                    picture_count=dom["picture_count"],
                    renderer=renderer,
                    threshold_version=self.config.version,
                    provenance=dict(provenance or {}),
                )

        metrics = _metric_values(metric_report)
        if not metrics:
            return GateDecision(
                QualityStatus.NEEDS_REVIEW,
                reasons=[
                    "no metric report supplied; visual thresholds are not established"
                ],
                picture_count=dom.get("picture_count", 0),
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )
        if not _metric_passes(metrics, self.config):
            failed = []
            if metrics.get("ssim", 0.0) < self.config.min_ssim:
                failed.append("SSIM below threshold")
            if (
                metrics.get("explicit_error_rate", 1.0)
                >= self.config.max_explicit_error_rate
            ):
                failed.append("explicit error rate above threshold")
            if metrics.get("edge_f1", 0.0) < self.config.min_edge_f1:
                failed.append("edge F1 below threshold")
            if metrics.get("color_delta", float("inf")) > self.config.max_color_delta:
                failed.append("mean color Delta E00 above threshold")
            if metrics.get("color_delta_p95", 0.0) > self.config.max_color_delta_p95:
                failed.append("P95 color Delta E00 above threshold")
            reasons.extend(failed or ["one or more visual thresholds failed"])
            return GateDecision(
                QualityStatus.FAIL,
                reasons=reasons,
                picture_count=dom.get("picture_count", 0),
                metrics=metrics,
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )

        block_reports = _value(metric_report, "block_reports", []) or []
        if isinstance(metric_report, Mapping):
            block_reports = metric_report.get("block_reports", block_reports) or []
        if any(not bool(_value(item, "passed", False)) for item in block_reports):
            return GateDecision(
                QualityStatus.FAIL,
                reasons=["one or more Block metrics failed"],
                picture_count=dom.get("picture_count", 0),
                metrics=metrics,
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )

        low = _low_confidence(scene, self.config.min_confidence)
        if low:
            return GateDecision(
                QualityStatus.NEEDS_REVIEW,
                reasons=low,
                picture_count=dom.get("picture_count", 0),
                metrics=metrics,
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )

        # The only path to PASS is a successful, native PowerPoint render.
        # LibreOffice is useful evidence, but can never be the final truth.
        if str(renderer).lower() in ("libreoffice", "lo", "wps", "wpsoffice"):
            return GateDecision(
                QualityStatus.PREVERIFIED,
                passed=False,
                reasons=["%s verification is not PowerPoint acceptance" % renderer],
                picture_count=dom.get("picture_count", 0),
                metrics=metrics,
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )
        acceptance_eligible = bool(_value(render_result, "acceptance_eligible", False))
        if (
            str(renderer).lower() not in ("powerpoint", "microsoft_powerpoint", "ppt")
            or not acceptance_eligible
        ):
            return GateDecision(
                QualityStatus.NEEDS_REVIEW,
                reasons=["PowerPoint final render is required for PASS"],
                picture_count=dom.get("picture_count", 0),
                metrics=metrics,
                renderer=renderer,
                threshold_version=self.config.version,
                provenance=dict(provenance or {}),
            )
        return GateDecision(
            QualityStatus.PASS,
            passed=True,
            picture_count=dom.get("picture_count", 0),
            metrics=metrics,
            renderer=renderer,
            threshold_version=self.config.version,
            provenance=dict(provenance or {}),
        )

    check = evaluate
