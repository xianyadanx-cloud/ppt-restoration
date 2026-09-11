"""Deterministic, dependency-light visual metrics for rendered slides."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from PIL import Image, ImageChops, ImageFilter, ImageStat

from ppt_restore.rendering.renderers import RenderResult

ImageLike = Union[Image.Image, os.PathLike, str]


DEFAULT_METRIC_THRESHOLDS: Dict[str, float] = {
    "version": "1.0",
    "ssim": 0.92,
    "explicit_error_rate": 0.05,
    "edge_f1": 0.80,
    "bbox_iou": 0.95,
    "center_error_px": 2.0,
    "color_delta": 3.0,
    "color_delta_p95": 8.0,
}


def _load_image(value: Any) -> Image.Image:
    if isinstance(value, Image.Image):
        return value.convert("RGB")
    if isinstance(value, RenderResult):
        if not value.images:
            raise FileNotFoundError("RenderResult contains no rendered images")
        value = value.images[0]
    if isinstance(value, (list, tuple)):
        if not value:
            raise FileNotFoundError("No rendered images supplied")
        value = value[0]
    path = Path(value)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with Image.open(path) as image:
        return image.convert("RGB")


def _aligned_images(
    render: Image.Image, truth: Image.Image
) -> Tuple[Image.Image, Image.Image]:
    if render.size == truth.size:
        return render, truth
    return render.resize(truth.size, Image.Resampling.BILINEAR), truth


def calculate_mse(render: Image.Image, truth: Image.Image) -> float:
    render, truth = _aligned_images(render.convert("RGB"), truth.convert("RGB"))
    diff = ImageChops.difference(render, truth)
    stat = ImageStat.Stat(diff)
    return sum(stat.sum2) / float(max(1, render.width * render.height * 3))


def calculate_ssim(render: Image.Image, truth: Image.Image, window: int = 8) -> float:
    """Compute a stable luminance SSIM approximation over small windows."""

    render, truth = _aligned_images(render.convert("L"), truth.convert("L"))
    width, height = render.size
    if not width or not height:
        return 1.0
    # A single global window is too forgiving for small local errors.  Average
    # windows gives the metric useful locality while remaining dependency-free.
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    values: List[float] = []
    for top in range(0, height, max(1, window)):
        for left in range(0, width, max(1, window)):
            box = (left, top, min(width, left + window), min(height, top + window))
            a = list(render.crop(box).getdata())
            b = list(truth.crop(box).getdata())
            if not a:
                continue
            mean_a = sum(a) / len(a)
            mean_b = sum(b) / len(b)
            var_a = sum((value - mean_a) ** 2 for value in a) / len(a)
            var_b = sum((value - mean_b) ** 2 for value in b) / len(b)
            cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b)) / len(a)
            denominator = (mean_a * mean_a + mean_b * mean_b + c1) * (
                var_a + var_b + c2
            )
            numerator = (2 * mean_a * mean_b + c1) * (2 * cov + c2)
            values.append(numerator / denominator if denominator else 1.0)
    return max(0.0, min(1.0, sum(values) / len(values))) if values else 1.0


def calculate_explicit_error_rate(
    render: Image.Image, truth: Image.Image, delta: int = 16
) -> float:
    render, truth = _aligned_images(render.convert("RGB"), truth.convert("RGB"))
    a = list(render.getdata())
    b = list(truth.getdata())
    if not a:
        return 0.0
    errors = sum(
        1 for x, y in zip(a, b) if max(abs(x[i] - y[i]) for i in range(3)) > delta
    )
    return errors / float(len(a))


def _edge_mask(image: Image.Image, threshold: int = 30) -> Image.Image:
    edge = image.convert("L").filter(ImageFilter.FIND_EDGES)
    return edge.point(lambda value: 255 if value >= threshold else 0)


def calculate_edge_f1(
    render: Image.Image, truth: Image.Image, threshold: int = 30
) -> float:
    render, truth = _aligned_images(render.convert("RGB"), truth.convert("RGB"))
    a = list(_edge_mask(render, threshold).getdata())
    b = list(_edge_mask(truth, threshold).getdata())
    true_positive = sum(1 for x, y in zip(a, b) if x and y)
    predicted = sum(1 for x in a if x)
    actual = sum(1 for y in b if y)
    if predicted == 0 and actual == 0:
        return 1.0
    precision = true_positive / float(predicted) if predicted else 0.0
    recall = true_positive / float(actual) if actual else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _rgb_to_lab(rgb: Sequence[int]) -> Tuple[float, float, float]:
    values = []
    for channel in rgb[:3]:
        value = float(channel) / 255.0
        values.append(
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = values
    x = (red * 0.4124564 + green * 0.3575761 + blue * 0.1804375) / 0.95047
    y = red * 0.2126729 + green * 0.7151522 + blue * 0.0721750
    z = (red * 0.0193339 + green * 0.1191920 + blue * 0.9503041) / 1.08883
    epsilon, kappa = 216.0 / 24389.0, 24389.0 / 27.0
    transform = lambda value: (
        value ** (1.0 / 3.0) if value > epsilon else (kappa * value + 16.0) / 116.0
    )
    fx, fy, fz = transform(x), transform(y), transform(z)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)


def _delta_e00(first: Sequence[float], second: Sequence[float]) -> float:
    l1, a1, b1 = first
    l2, a2, b2 = second
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    cbar = (c1 + c2) / 2.0
    g = 0.5 * (1.0 - math.sqrt(cbar**7 / (cbar**7 + 25.0**7)))
    ap1, ap2 = (1.0 + g) * a1, (1.0 + g) * a2
    cp1, cp2 = math.hypot(ap1, b1), math.hypot(ap2, b2)
    hp1 = math.degrees(math.atan2(b1, ap1)) % 360.0 if cp1 else 0.0
    hp2 = math.degrees(math.atan2(b2, ap2)) % 360.0 if cp2 else 0.0
    dl, dc = l2 - l1, cp2 - cp1
    dh_angle = hp2 - hp1
    if cp1 * cp2 == 0:
        dh_angle = 0.0
    elif dh_angle > 180.0:
        dh_angle -= 360.0
    elif dh_angle < -180.0:
        dh_angle += 360.0
    dh = 2.0 * math.sqrt(cp1 * cp2) * math.sin(math.radians(dh_angle / 2.0))
    lbar, cpbar = (l1 + l2) / 2.0, (cp1 + cp2) / 2.0
    if cp1 * cp2 == 0:
        hpbar = hp1 + hp2
    elif abs(hp1 - hp2) <= 180.0:
        hpbar = (hp1 + hp2) / 2.0
    elif hp1 + hp2 < 360.0:
        hpbar = (hp1 + hp2 + 360.0) / 2.0
    else:
        hpbar = (hp1 + hp2 - 360.0) / 2.0
    t = (
        1.0
        - 0.17 * math.cos(math.radians(hpbar - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * hpbar))
        + 0.32 * math.cos(math.radians(3.0 * hpbar + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * hpbar - 63.0))
    )
    sl = 1.0 + 0.015 * (lbar - 50.0) ** 2 / math.sqrt(20.0 + (lbar - 50.0) ** 2)
    sc, sh = 1.0 + 0.045 * cpbar, 1.0 + 0.015 * cpbar * t
    rt = (
        -2.0
        * math.sqrt(cpbar**7 / (cpbar**7 + 25.0**7))
        * math.sin(math.radians(60.0 * math.exp(-(((hpbar - 275.0) / 25.0) ** 2))))
    )
    return math.sqrt(
        (dl / sl) ** 2 + (dc / sc) ** 2 + (dh / sh) ** 2 + rt * (dc / sc) * (dh / sh)
    )


def calculate_color_delta(render: Image.Image, truth: Image.Image) -> Dict[str, float]:
    """Return deterministic CIEDE2000 mean and P95 values in sRGB/D65."""

    render, truth = _aligned_images(render.convert("RGB"), truth.convert("RGB"))
    first, second = list(render.getdata()), list(truth.getdata())
    # Bound CPU cost on full-size slides while sampling a stable grid.
    stride = max(1, int(math.ceil(math.sqrt(max(1, len(first)) / 100000.0))))
    distances = [
        _delta_e00(_rgb_to_lab(a), _rgb_to_lab(b))
        for a, b in zip(first[::stride], second[::stride])
    ]
    if not distances:
        return {"mean": 0.0, "p95": 0.0}
    distances.sort()
    index = min(len(distances) - 1, int(math.ceil(len(distances) * 0.95)) - 1)
    return {"mean": sum(distances) / len(distances), "p95": distances[index]}


def calculate_mse_and_ssim(img1: Image.Image, img2: Image.Image) -> Tuple[float, float]:
    """Backward-compatible pair used by the legacy verification scripts."""

    return round(calculate_mse(img1, img2), 6), round(calculate_ssim(img1, img2), 6)


def bbox_iou(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != 4 or len(second) != 4:
        return 0.0
    ax, ay, aw, ah = [float(value) for value in first]
    bx, by, bw, bh = [float(value) for value in second]
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = max(0.0, aw) * max(0.0, ah) + max(0.0, bw) * max(0.0, bh) - intersection
    return intersection / union if union else (1.0 if first == second else 0.0)


def bbox_center_error(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != 4 or len(second) != 4:
        return float("inf")
    ac = (
        float(first[0]) + float(first[2]) / 2.0,
        float(first[1]) + float(first[3]) / 2.0,
    )
    bc = (
        float(second[0]) + float(second[2]) / 2.0,
        float(second[1]) + float(second[3]) / 2.0,
    )
    return math.hypot(ac[0] - bc[0], ac[1] - bc[1])


def _get(mapping_or_obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(mapping_or_obj, Mapping):
        return mapping_or_obj.get(key, default)
    return getattr(mapping_or_obj, key, default)


def _bbox(element: Any) -> Optional[Sequence[float]]:
    for key in ("layout_bbox_px", "bbox_px", "bbox", "visual_bbox_px"):
        candidate = _get(element, key)
        if candidate is not None and len(candidate) == 4:
            return candidate
    return None


def _blocks(scene: Any) -> List[Any]:
    values = _get(scene, "blocks", None)
    if values is None and _get(scene, "nodes", None) is not None:
        # SceneSpec v2 expresses macro regions as semantic group nodes.  Do
        # not score every glyph-sized text node independently: that recreates
        # the original analyzer's fragmentation problem.  If the host agent
        # did not emit groups, score one deterministic full-slide region.
        nodes = list(_get(scene, "nodes", ()) or ())
        groups = [
            node
            for node in nodes
            if str(_get(node, "kind", "")) == "group"
            and not _get(node, "parent_id", None)
        ]
        if groups:
            return groups
        canvas = _get(scene, "canvas", {}) or {}
        width = _get(canvas, "width_px", 0) or 0
        height = _get(canvas, "height_px", 0) or 0
        return [{"id": "slide", "bbox_px": [0, 0, width, height]}]
    values = values or []
    if isinstance(values, Mapping):
        values = list(values.values())
    else:
        values = list(values)
    canvas = _get(scene, "canvas", {}) or {}
    width = float(_get(canvas, "width_px", 0) or 0)
    height = float(_get(canvas, "height_px", 0) or 0)
    normalized = []
    for block in values:
        if (
            isinstance(block, Mapping)
            and block.get("bbox_px") is None
            and block.get("bbox_norm") is not None
            and width > 0
            and height > 0
        ):
            item = dict(block)
            left, top, box_width, box_height = [
                float(value) for value in item["bbox_norm"]
            ]
            item["bbox_px"] = [
                left * width / 1000.0,
                top * height / 1000.0,
                box_width * width / 1000.0,
                box_height * height / 1000.0,
            ]
            normalized.append(item)
        else:
            normalized.append(block)
    return normalized


def _crop(image: Image.Image, box: Sequence[float], scene: Any) -> Image.Image:
    width, height = image.size
    canvas = _get(scene, "canvas", None)
    canvas_width = (
        _get(canvas, "width_px", None) or _get(canvas, "width", None) or width
    )
    canvas_height = (
        _get(canvas, "height_px", None) or _get(canvas, "height", None) or height
    )
    coordinate_system = _get(canvas, "coordinate_system", None) or _get(
        scene, "coordinate_system", None
    )
    values = [float(value) for value in box]
    if coordinate_system in ("norm", "normalized", "0-1000") or (
        max(values) <= 1000 and canvas_width == 1000
    ):
        left, top, bw, bh = (
            values[0] * width / 1000.0,
            values[1] * height / 1000.0,
            values[2] * width / 1000.0,
            values[3] * height / 1000.0,
        )
    else:
        left, top = (
            values[0] * width / float(canvas_width),
            values[1] * height / float(canvas_height),
        )
        bw, bh = (
            values[2] * width / float(canvas_width),
            values[3] * height / float(canvas_height),
        )
    return image.crop(
        (
            max(0, int(left)),
            max(0, int(top)),
            min(width, int(left + bw)),
            min(height, int(top + bh)),
        )
    )


@dataclass
class MetricReport:
    metrics: Dict[str, Any] = field(default_factory=dict)
    block_reports: List[Dict[str, Any]] = field(default_factory=list)
    passed: bool = False
    thresholds: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_METRIC_THRESHOLDS)
    )
    errors: List[str] = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        if key in self.metrics:
            return self.metrics[key]
        if key == "block_reports":
            return self.block_reports
        if key == "passed":
            return self.passed
        if key == "thresholds":
            return self.thresholds
        raise KeyError(key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": dict(self.metrics),
            "block_reports": list(self.block_reports),
            "passed": self.passed,
            "thresholds": dict(self.thresholds),
            "errors": list(self.errors),
        }


class MetricEngine:
    """Evaluate full-slide and per-block visual metrics."""

    def __init__(self, thresholds: Optional[Mapping[str, Any]] = None):
        self.thresholds = dict(DEFAULT_METRIC_THRESHOLDS)
        if thresholds:
            self.thresholds.update(dict(thresholds))

    def evaluate(
        self, scene: Any, ground_truth: ImageLike, render: Any, **kwargs: Any
    ) -> MetricReport:
        try:
            truth = _load_image(ground_truth)
            rendered = _load_image(render)
        except (OSError, ValueError) as exc:
            return MetricReport(
                passed=False,
                thresholds=dict(self.thresholds),
                errors=["input/render image unavailable: %s" % exc],
            )
        rendered, truth = _aligned_images(rendered, truth)
        color = calculate_color_delta(rendered, truth)
        metrics: Dict[str, Any] = {
            "mse": calculate_mse(rendered, truth),
            "ssim": calculate_ssim(rendered, truth),
            "edge_f1": calculate_edge_f1(rendered, truth),
            "explicit_error_rate": calculate_explicit_error_rate(rendered, truth),
            "color_delta_ciede2000": color,
            "color_delta": color["mean"],
            "color_delta_p95": color["p95"],
            "size": list(truth.size),
        }
        block_reports: List[Dict[str, Any]] = []
        for index, block in enumerate(_blocks(scene), 1):
            block_box = _bbox(block)
            if not block_box:
                continue
            gt_crop = _crop(truth, block_box, scene)
            render_crop = _crop(rendered, block_box, scene)
            block_color = calculate_color_delta(render_crop, gt_crop)
            block_metrics = {
                "mse": calculate_mse(render_crop, gt_crop),
                "ssim": calculate_ssim(render_crop, gt_crop),
                "edge_f1": calculate_edge_f1(render_crop, gt_crop),
                "explicit_error_rate": calculate_explicit_error_rate(
                    render_crop, gt_crop
                ),
                "color_delta": block_color["mean"],
                "color_delta_p95": block_color["p95"],
            }
            expected = (
                _get(block, "ground_truth_bbox_px", None)
                or _get(block, "reference_bbox", None)
                or _get(block, "expected_bbox_px", None)
            )
            actual = (
                _get(block, "render_bbox_px", None)
                or _get(block, "compiled_bbox_px", None)
                or _get(block, "actual_bbox_px", None)
            )
            if expected is not None and actual is not None:
                block_metrics["bbox_iou"] = bbox_iou(expected, actual)
                block_metrics["center_error_px"] = bbox_center_error(expected, actual)
            block_reports.append(
                {
                    "block_id": _get(block, "id", None)
                    or _get(block, "block_id", index),
                    "bbox": list(block_box),
                    "metrics": block_metrics,
                    "passed": self._passes(block_metrics),
                }
            )
        passed = self._passes(metrics) and all(item["passed"] for item in block_reports)
        return MetricReport(
            metrics=metrics,
            block_reports=block_reports,
            passed=passed,
            thresholds=dict(self.thresholds),
        )

    def _passes(self, metrics: Mapping[str, Any]) -> bool:
        if "ssim" in metrics and metrics["ssim"] < self.thresholds["ssim"]:
            return False
        if (
            "explicit_error_rate" in metrics
            and metrics["explicit_error_rate"] >= self.thresholds["explicit_error_rate"]
        ):
            return False
        if "edge_f1" in metrics and metrics["edge_f1"] < self.thresholds["edge_f1"]:
            return False
        if "bbox_iou" in metrics and metrics["bbox_iou"] < self.thresholds["bbox_iou"]:
            return False
        if (
            "center_error_px" in metrics
            and metrics["center_error_px"] > self.thresholds["center_error_px"]
        ):
            return False
        if (
            "color_delta" in metrics
            and metrics["color_delta"] > self.thresholds["color_delta"]
        ):
            return False
        if (
            "color_delta_p95" in metrics
            and metrics["color_delta_p95"] > self.thresholds["color_delta_p95"]
        ):
            return False
        return True
