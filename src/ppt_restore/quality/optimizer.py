"""Deterministic, bounded Scene IR parameter search.

The optimizer never writes source code and never asks an LLM to choose values.
It clones a scene, edits an explicit whitelist, and delegates rendering and
loss calculation to injected callbacks.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence


@dataclass
class OptimizationResult:
    scene: Any
    block_id: str
    objective: float
    rounds: int = 0
    candidates_evaluated: int = 0
    improved: bool = False
    stopped_reason: str = ""
    cache_hits: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def best_scene(self):
        return self.scene

    @property
    def best_loss(self):
        return self.objective

    def to_dict(self):
        return {
            "block_id": self.block_id,
            "objective": self.objective,
            "rounds": self.rounds,
            "candidates_evaluated": self.candidates_evaluated,
            "improved": self.improved,
            "stopped_reason": self.stopped_reason,
            "cache_hits": self.cache_hits,
            "history": self.history,
        }


def _get(obj, key, default=None):
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj, key, value):
    if isinstance(obj, Mapping):
        obj[key] = value
    else:
        try:
            setattr(obj, key, value)
        except (AttributeError, TypeError):
            # Scene dataclasses are intentionally immutable for validation;
            # clones can safely be edited through their low-level setter.
            object.__setattr__(obj, key, value)


def _scene_dict(scene):
    if hasattr(scene, "to_dict"):
        return scene.to_dict()
    if isinstance(scene, Mapping):
        return scene
    return getattr(scene, "__dict__", repr(scene))


class Optimizer:
    STEP_SIZES = (16, 8, 4, 2, 1)
    WHITELIST = frozenset(
        {
            "x",
            "y",
            "left",
            "top",
            "width",
            "height",
            "w",
            "h",
            "font_size_pt",
            "font_size",
            "line_spacing",
            "line_spacing_pt",
            "space_before_pt",
            "space_after_pt",
            "margin_pt",
            "margins_pt",
            "corner_radius_px",
            "line_width_px",
            "fill",
            "fill_color",
            "gradient_angle",
            "opacity",
            "fill_opacity",
            "line_opacity",
            "shadow",
            "glow",
        }
    )

    def __init__(
        self,
        render: Optional[Callable] = None,
        max_rounds: int = 5,
        max_candidates: int = 32,
        cache: Optional[Dict[str, float]] = None,
        cache_context: Optional[Mapping[str, Any]] = None,
    ):
        self.render = render
        self.max_rounds = min(5, max(1, int(max_rounds)))
        self.max_candidates = min(32, max(1, int(max_candidates)))
        self.cache: Dict[str, float] = cache if cache is not None else {}
        self.cache_hits = 0
        self.cache_context = dict(cache_context or {})

    def optimize(
        self,
        scene: Any,
        block_id: str,
        objective: Optional[Callable] = None,
        render: Optional[Callable] = None,
        variables: Optional[Sequence[str]] = None,
        priority_node_ids: Optional[Sequence[str]] = None,
    ) -> OptimizationResult:
        if objective is None:
            raise ValueError("optimization requires an explicit objective")
        if not self._elements(scene, block_id):
            raise ValueError("unknown or empty optimization block: %s" % block_id)
        render = render if render is not None else self.render
        allowed = set(variables or self.WHITELIST) & self.WHITELIST
        current = copy.deepcopy(scene)
        current_loss = self._evaluate(current, block_id, objective, render)
        result = OptimizationResult(
            current, str(block_id), current_loss, cache_hits=self.cache_hits
        )
        low_gain_rounds = 0
        for round_no, step in enumerate(self.STEP_SIZES[: self.max_rounds], 1):
            best = current
            best_loss = current_loss
            evaluated = 0
            specs = self._variable_specs(current, block_id, allowed)
            if specs and priority_node_ids:
                grouped = {}
                for spec in specs:
                    grouped.setdefault(str(_get(spec[0], "id")), []).append(spec)
                ranked = list(
                    dict.fromkeys(
                        str(node_id)
                        for node_id in priority_node_ids
                        if str(node_id) in grouped
                    )
                )
                ranked += [node_id for node_id in grouped if node_id not in ranked]
                # Distribute the first candidate pair across nodes before
                # spending the budget on every field of a single node.
                specs = []
                for index in range(max(map(len, grouped.values()))):
                    for node_id in ranked:
                        fields = grouped[node_id]
                        if index < len(fields):
                            specs.append(fields[(index + round_no - 1) % len(fields)])
            elif specs:
                offset = ((round_no - 1) * max(1, self.max_candidates // 2)) % len(
                    specs
                )
                specs = specs[offset:] + specs[:offset]
            for target, key, base in specs:
                for delta in (-step, step):
                    if evaluated >= self.max_candidates:
                        break
                    candidate = copy.deepcopy(current)
                    # Specs retain an element reference from ``current``;
                    # resolve its stable id in the cloned candidate before
                    # applying a trial so candidates never mutate the parent.
                    trial_target = self._clone_target(candidate, target, block_id)
                    if trial_target is not None and self._apply(
                        trial_target, key, base, delta
                    ):
                        evaluated += 1
                        try:
                            loss = self._evaluate(
                                candidate, block_id, objective, render
                            )
                        except (ValueError, RuntimeError) as exc:
                            result.history.append(
                                {
                                    "round": round_no,
                                    "candidate_rejected": str(exc),
                                    "node_id": _get(target, "id"),
                                    "field": list(key),
                                    "delta": delta,
                                    "scene_sha256": self.scene_hash(candidate),
                                }
                            )
                            continue
                        result.history.append(
                            {
                                "round": round_no,
                                "candidate_loss": loss,
                                "node_id": _get(target, "id"),
                                "field": list(key),
                                "delta": delta,
                                "scene_sha256": self.scene_hash(candidate),
                            }
                        )
                        if loss < best_loss - 1e-12:
                            best, best_loss = candidate, loss
                    if evaluated >= self.max_candidates:
                        break
                if evaluated >= self.max_candidates:
                    break
            gain = current_loss - best_loss
            result.rounds = round_no
            result.candidates_evaluated += evaluated
            result.history.append(
                {
                    "round": round_no,
                    "step": step,
                    "loss_before": current_loss,
                    "loss_after": best_loss,
                    "gain": gain,
                    "candidates": evaluated,
                }
            )
            if gain > 0:
                current, current_loss = best, best_loss
                result.improved = True
            if gain <= max(1e-12, abs(current_loss) * 0.002):
                low_gain_rounds += 1
            else:
                low_gain_rounds = 0
            if low_gain_rounds >= 2:
                result.stopped_reason = "two_consecutive_rounds_below_0.2%"
                break
        if not result.stopped_reason:
            result.stopped_reason = "max_rounds"
        result.scene = current
        result.objective = current_loss
        result.cache_hits = self.cache_hits
        return result

    def _evaluate(self, scene, block_id, objective, render):
        context = json.dumps(self.cache_context, sort_keys=True, default=str)
        cache_key = (
            self.scene_hash(scene)
            + ":"
            + str(block_id)
            + ":"
            + context
            + ":"
            + str(id(objective))
        )
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        rendered = render(scene, block_id) if render is not None else scene
        fn = objective
        # Support objective(scene), objective(scene, rendered), and
        # objective(scene, block_id, rendered) without requiring adapters.
        try:
            count = len(inspect.signature(fn).parameters)
        except Exception:
            count = 1
        if count >= 3:
            value = fn(scene, block_id, rendered)
        elif count == 2:
            value = fn(scene, rendered)
        else:
            value = fn(rendered)
        if isinstance(value, Mapping):
            metric_key = next(
                (key for key in ("loss", "objective", "score") if key in value), None
            )
            if metric_key is None:
                raise ValueError("objective result is missing a numeric loss")
            value = value[metric_key]
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("objective must return a finite loss")
        self.cache[cache_key] = value
        return value

    def _variable_specs(self, scene, block_id, allowed):
        specs = []
        for element in self._elements(scene, block_id):
            bbox = _get(
                element,
                "layout_bbox_px",
                _get(element, "bbox_px", _get(element, "bbox", None)),
            )
            if bbox is not None and len(bbox) == 4:
                for key, idx in (("left", 0), ("top", 1), ("width", 2), ("height", 3)):
                    if key in allowed:
                        specs.append((element, ("bbox", idx), float(bbox[idx])))
            for key in (
                "font_size_pt",
                "font_size",
                "line_spacing",
                "line_spacing_pt",
                "space_before_pt",
                "space_after_pt",
                "corner_radius_px",
                "line_width_px",
                "gradient_angle",
                "opacity",
                "fill_opacity",
                "line_opacity",
            ):
                value = _get(element, key, None)
                if value is None:
                    style = _get(
                        element,
                        "shape_style",
                        _get(element, "text_style", _get(element, "style", None)),
                    )
                    value = _get(style, key, None) if style is not None else None
                    target = element
                    target_key = ("style", key) if value is not None else ("key", key)
                else:
                    target = element
                if (
                    value is not None
                    and key in allowed
                    and isinstance(value, (int, float))
                ):
                    if _get(element, key, None) is not None:
                        target_key = ("key", key)
                    specs.append((target, target_key, float(value)))
        return specs

    def _elements(self, scene, block_id):
        direct = _get(scene, "elements", None)
        if direct is not None:
            return list(direct)
        nodes = _get(scene, "nodes", None)
        if nodes is not None:
            nodes = list(nodes or ())
            owned = [
                node
                for node in nodes
                if str(_get(node, "block_id", "")) == str(block_id)
            ]
            if owned:
                ids = {str(_get(node, "id", "")) for node in owned}
                while True:
                    children = [
                        node
                        for node in nodes
                        if str(_get(node, "parent_id", "")) in ids
                        and _get(node, "block_id", None) in (None, "", block_id)
                    ]
                    expanded = ids | {str(_get(node, "id", "")) for node in children}
                    if expanded == ids:
                        break
                    ids = expanded
                return [node for node in nodes if str(_get(node, "id", "")) in ids]
            groups = [
                node
                for node in nodes
                if str(_get(node, "id", "")) == str(block_id)
                and str(_get(node, "kind", "")) == "group"
            ]
            if groups:
                group_id = str(block_id)
                return [
                    node
                    for node in nodes
                    if str(_get(node, "id", "")) == group_id
                    or str(_get(node, "parent_id", "")) == group_id
                ]
            # Unknown v2 targets must never become a whole-slide search.
            return []
        for block in _get(scene, "blocks", ()) or ():
            if str(_get(block, "id", "")) == str(block_id):
                return list(_get(block, "elements", ()) or ())
        return []

    def _clone_target(self, scene, original, block_id):
        """Find the corresponding element in a deepcopy by stable id."""
        original_id = _get(original, "id", None)
        if original_id is not None:
            for element in self._elements(scene, block_id):
                if str(_get(element, "id", "")) == str(original_id):
                    return element
        return None

    def _apply(self, target, key, base, delta):
        kind, value_key = key
        if kind == "bbox":
            bbox = list(
                _get(
                    target,
                    "layout_bbox_px",
                    _get(target, "bbox_px", _get(target, "bbox", None)),
                )
            )
            idx = value_key
            value = base + delta
            if idx in (2, 3):
                value = max(1.0, value)
            bbox[idx] = value
            field = (
                "layout_bbox_px"
                if _get(target, "layout_bbox_px", None) is not None
                else "bbox_px"
                if _get(target, "bbox_px", None) is not None
                else "bbox"
            )
            _set(target, field, bbox)
            return True
        if kind == "style":
            style = None
            for style_key in (
                "shape_style",
                "shapeStyle",
                "text_style",
                "textStyle",
                "style",
            ):
                style = _get(target, style_key, None)
                if style is not None and _get(style, value_key, None) is not None:
                    break
            if style is None:
                return False
            target = style
        value = (
            base + delta
            if value_key not in ("opacity", "fill_opacity", "line_opacity")
            else min(1.0, max(0.0, base + delta / 100.0))
        )
        if value_key == "line_spacing":
            value = base + delta / 100.0
        if (
            value_key
            in ("font_size_pt", "font_size", "line_spacing", "line_spacing_pt")
            and value <= 0
        ):
            return False
        if (
            value_key
            in (
                "space_before_pt",
                "space_after_pt",
                "corner_radius_px",
                "line_width_px",
            )
            and value < 0
        ):
            return False
        _set(target, value_key, value)
        return True

    def scene_hash(self, scene) -> str:
        return hashlib.sha256(
            json.dumps(
                _scene_dict(scene), sort_keys=True, ensure_ascii=False, default=str
            ).encode("utf-8")
        ).hexdigest()

    def cached_evaluate(self, scene, evaluate: Callable) -> float:
        key = self.scene_hash(scene)
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        value = float(evaluate(scene))
        self.cache[key] = value
        return value


__all__ = ["Optimizer", "OptimizationResult"]
