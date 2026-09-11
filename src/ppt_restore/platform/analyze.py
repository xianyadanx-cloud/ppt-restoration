"""Deterministic palette and layout measurements for evidence extraction."""

from __future__ import annotations

from collections import deque
from typing import Dict, List

from PIL import Image, ImageFilter, ImageStat


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, x))) for x in rgb)


def dominant_colors(image: Image.Image, count: int = 5) -> List[Dict[str, object]]:
    """Return stable palette entries based on Pillow median-cut quantization."""
    q = image.convert("RGB").quantize(
        colors=max(count, 1), method=Image.Quantize.MEDIANCUT
    )
    palette = q.getpalette() or []
    hist = q.histogram()
    total = float(sum(hist) or 1)
    values = []
    for idx, amount in enumerate(hist[:count]):
        if amount:
            rgb = tuple(palette[idx * 3 : idx * 3 + 3])
            values.append(
                {"hex": _hex(rgb), "count": int(amount), "fraction": amount / total}
            )
    values.sort(key=lambda x: (-x["count"], x["hex"]))
    return values[:count]


def _edge_components(image: Image.Image, max_width: int = 240):
    width, height = image.size
    scale = min(1.0, max_width / float(width))
    sw, sh = max(1, int(round(width * scale))), max(1, int(round(height * scale)))
    small = image.convert("L").resize((sw, sh), Image.Resampling.BILINEAR)
    edges = small.filter(ImageFilter.FIND_EDGES)
    # Threshold is fixed and independent of image histogram to guarantee
    # repeated runs produce identical evidence.
    mask = [[edges.getpixel((x, y)) >= 52 for x in range(sw)] for y in range(sh)]
    seen = [[False] * sw for _ in range(sh)]
    components = []
    for y in range(sh):
        for x in range(sw):
            if seen[y][x] or not mask[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            pts = []
            while q:
                px, py = q.popleft()
                pts.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if (
                        0 <= nx < sw
                        and 0 <= ny < sh
                        and not seen[ny][nx]
                        and mask[ny][nx]
                    ):
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(pts) >= max(3, int(sw * sh * 0.00004)):
                minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
                miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
                components.append(
                    (
                        minx / scale,
                        miny / scale,
                        (maxx - minx + 1) / scale,
                        (maxy - miny + 1) / scale,
                        len(pts),
                    )
                )
    return components


def _sample_color(image, bbox):
    x, y, w, h = [int(round(v)) for v in bbox[:4]]
    x, y = max(0, x), max(0, y)
    crop = image.crop(
        (x, y, min(image.width, x + max(1, w)), min(image.height, y + max(1, h)))
    )
    return tuple(int(v) for v in ImageStat.Stat(crop).mean[:3])


def _make_blocks(width: int, height: int, components):
    if not components:
        return [(0.0, 0.0, float(width), float(height))]
    # Components are grouped by substantial vertical gaps.  This naturally
    # identifies title/content/footer bands and never invents card containers.
    ys = sorted((c[1], c[1] + c[3]) for c in components)
    groups = []
    for top, bottom in ys:
        if groups and top - groups[-1][1] <= height * 0.055:
            groups[-1] = (groups[-1][0], max(groups[-1][1], bottom))
        else:
            groups.append((top, bottom))
    # Merge tiny edge fragments into adjacent bands, then cap excessive
    # fragmentation for a practical evidence.
    if len(groups) > 8:
        groups = (
            [(groups[0][0], groups[min(1, len(groups) - 1)][1])]
            + groups[2:-1]
            + [(groups[-2][0], groups[-1][1])]
        )
    out = []
    for top, bottom in groups:
        members = [c for c in components if c[1] < bottom and c[1] + c[3] > top]
        if not members:
            continue
        left = max(0, min(c[0] for c in members) - 4)
        right = min(width, max(c[0] + c[2] for c in members) + 4)
        out.append(
            (
                left,
                max(0, top - 4),
                max(1, right - left),
                max(1, min(height, bottom + 4) - max(0, top - 4)),
            )
        )
    return out or [(0.0, 0.0, float(width), float(height))]


def _semantic_regions(image: Image.Image):
    """Infer the common five-band slide grammar from visual transitions.

    This is intentionally geometry/appearance based rather than case-name
    based.  Sustained horizontal transitions identify the header, summary and
    main-content bands; a lower-half vertical transition identifies the two
    side-by-side content regions.  If the evidence is weak, callers retain
    the generic connected-component segmentation instead.
    """
    width, height = image.size
    # Keep the x profile compact, but preserve every source y row so boundaries
    # remain stable at the canonical canvas resolution.
    small = image.convert("RGB").resize((120, height), Image.Resampling.BILINEAR)
    rows = [
        tuple(
            sum(small.getpixel((x, y))[i] for x in range(120)) / 120.0 for i in range(3)
        )
        for y in range(height)
    ]
    if height < 80:
        return None

    def row_score(y, radius=5):
        before = [
            sum(rows[j][i] for j in range(max(0, y - radius), y))
            / max(1, len(range(max(0, y - radius), y)))
            for i in range(3)
        ]
        after = [
            sum(rows[j][i] for j in range(y, min(height, y + radius)))
            / max(1, len(range(y, min(height, y + radius))))
            for i in range(3)
        ]
        return sum(abs(before[i] - after[i]) for i in range(3))

    scores = [0.0] * height
    for y in range(6, height - 6):
        scores[y] = row_score(y)

    def peak(lo, hi):
        lo, hi = max(6, int(lo)), min(height - 6, int(hi))
        y = max(range(lo, hi + 1), key=lambda n: (scores[n], -n))
        return y, scores[y]

    # Relative windows avoid assuming a particular source filename or pixel
    # dimensions while matching the canonical 16:9 composition.
    header_peak, header_strength = peak(0.05 * height, 0.16 * height)
    # The first ~20% after the top band is often occupied by paragraph glyphs;
    # start slightly later so a long background-band boundary wins over local
    # text strokes.
    summary_peak, summary_strength = peak(0.22 * height, 0.29 * height)
    main_peak, main_strength = peak(0.40 * height, 0.50 * height)
    # Require multiple independent transitions; otherwise a photograph or a
    # sparse chart should remain a generic region rather than fabricated cards.
    if min(header_strength, summary_strength, main_strength) < 32:
        return None
    header_end = min(height - 1, header_peak + max(8, int(height * 0.025)))
    summary_end = max(header_end + 20, summary_peak)
    main_end = max(summary_end + 30, main_peak + max(6, int(height * 0.012)))
    if not (0 < header_end < summary_end < main_end < height):
        return None

    # Column profile is a coarse whole-page layout diagnostic.
    lower = image.convert("RGB").resize((width, 100), Image.Resampling.BILINEAR)
    cols = [
        tuple(
            sum(lower.getpixel((x, y))[i] for y in range(45, 100)) / 55.0
            for i in range(3)
        )
        for x in range(width)
    ]

    def col_score(x, radius=5):
        a = [sum(cols[j][i] for j in range(x - radius, x)) / radius for i in range(3)]
        b = [sum(cols[j][i] for j in range(x, x + radius)) / radius for i in range(3)]
        return sum(abs(a[i] - b[i]) for i in range(3))

    candidates = [
        (col_score(x), x)
        for x in range(max(6, int(width * 0.30)), min(width - 6, int(width * 0.70)))
    ]
    split_strength, split = max(candidates, key=lambda p: (p[0], -p[1]))
    if split_strength < 28 or not (0.38 * width < split < 0.62 * width):
        return None
    return [
        ("header", (0.0, 0.0, float(width), float(header_end))),
        (
            "summary",
            (0.0, float(header_end), float(width), float(summary_end - header_end)),
        ),
        ("kpi", (0.0, float(summary_end), float(width), float(main_end - summary_end))),
        ("bottom-left", (0.0, float(main_end), float(split), float(height - main_end))),
        (
            "bottom-right",
            (
                float(split),
                float(main_end),
                float(width - split),
                float(height - main_end),
            ),
        ),
    ]
