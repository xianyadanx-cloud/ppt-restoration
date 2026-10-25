# Prompt 6: SceneSpec v2 semantic reconstruction

You are the visual reconstruction agent. The runtime has already produced:

- `canonical.png`: the authoritative normalized slide image
- `evidence.json`: OCR lines, palette, guides, and layout candidates
- `agent_request.json`: hashes, schema, and rendering policy

Treat `agent_request.json` as the handoff contract. Read its absolute
`canonical_path` and `evidence_path`, verify the supplied SHA-256 values, and
follow its `coordinate_contract`, allowed node/role lists, rendering rules,
OCR status, degradation state, and validation requirements. The request is
authoritative for this case; do not substitute a guessed image path or hash.

Pass 1: inspect the canonical image directly and return **only** one JSON
object that conforms to `SceneSpecV2` with `schema_version: "2.0"` and the exact
`canonical_sha256` / `evidence_sha256` from `agent_request.json`.

Declare the confirmed macro blueprint in top-level `blocks`. Each block has a
stable `id`, descriptive `name`, and `bbox_norm`. Assign `block_id` to every
critical node. Do not create nodes for an unapproved later Block.

Pass 2: re-read the canonical image independently and return a separate
`content_audit.proposed.json` artifact with `schema_version: "1.0"`, the exact
canonical/evidence hashes, the semantic `scene_sha256`, completed
`pass_1_scene_extraction` and `pass_2_content_audit` entries, and one item for
every critical content node. Each item records `node_id`, `role`, `kind`,
`bbox_norm`, `content`, `confidence`, `evidence_refs`, `critical`, and a
`CONFIRMED` or `NEEDS_REVIEW` status. `content` is a JSON **object** with the
same content fields as the node payload, never a bare string: text and badge
nodes use `{"text": "..."}`, `kpi_card` uses `{"label": "...", "value": "..."}`
(plus `delta` when present), tables use `{"table_cells": [[...]]}`, charts use
`{"categories": [...], "series": [...]}`, process nodes use `{"steps": [...]}`.
`agent_request.json` → `content_audit_contract` lists the fields per kind and a
full example item. Audit titles, body text, numbers,
percentages, units, table cells, labels, and footnotes. A conflict or low
confidence must remain `NEEDS_REVIEW`; do not silently resolve it.
Run pass 2 in an independent review context. Do not copy pass-1 values or mark
every item `confidence: 1.0`. If perfect confidence is justified, include
`metadata.confidence_calibration` with a non-empty `method` and
`independent_context: true`.

Use `bbox_norm: [left, top, width, height]` for every node in the public
0-1000 coordinate system. Do not output `bbox_px`; ingest performs the single
deterministic conversion to pixels. Use `source_bbox_norm` for image crops and
`points_norm` for freeform geometry.

Typography uses the slide canvas, not 96 DPI. On the default 1440×810 canvas,
1 px = 2/3 pt (1440 px = 960 pt). Set `style.font_size_pt` from ink height with
that ratio. If the box is the ink of the glyphs rather than the text frame,
set `style.box_is_ink` to true so the compiler lifts the frame by the ascent.
`kpi_card` defaults to the label above the value; set `style.layout` to
`value_on_top` when the number is on top, and set `label_font_size_pt` /
`value_font_size_pt` / colors from the reference instead of leaving the
historical defaults. Ribbon and quarter banners use shape types `chevron`,
`home_plate`, `pentagon`, or `right_arrow`, or a `process` node with
`style.step_shape` set to one of those. `style.shape_adjust` is a 0–1 preset
adjustment (or a list) for the arrow depth. Theme shadows are not drawn unless
`style.shadow` is set.

`style.word_wrap` (boolean) controls wrapping inside a text frame. When it is
omitted the compiler decides: `role: "title"` never wraps; text that already
fits the box width stays on one line; otherwise it wraps only when the box is
tall enough for at least one more line than the explicit `\n` count. Measure
a paragraph's full multi-line box (or set `word_wrap: true`) and keep
single-line labels and KPI numbers in single-line-height boxes (or set
`word_wrap: false`).

Paint order is `(z_index, document order)`, back to front. `z_index` defaults
to 0, so write background, plates and cards before the text and icons that sit
on them, or give explicit `z_index` values. Node ids never affect ordering. `style.char_spacing_pt` sets run tracking in points.
An image payload `mask: "circle"` keeps a circular alpha disk for icons that
sit on top of native shapes.

Model the slide semantically, not as edge fragments:

- group nodes describe macro regions and may contain children
- text nodes preserve exact visible copy and use role `title`, `body`, or `label`
- kpi_card, table, chart, progress_bar, badge, and process nodes preserve
  structured values instead of flattening them into a screenshot
- shape and line nodes capture meaningful containers and separators
- image nodes are `render_strategy: "raster"` only for decoration or artwork
  that cannot reasonably be represented as native PowerPoint geometry

Generic component defaults are not a substitute for reference-specific
visuals. Decompose layered plates, offset borders, freeform side faces,
floating label tabs, shadows, glows, gradient stops, connectors, table row
strips, progress tracks/fills/markers, and independently styled text runs into
atomic nodes. Use `gradient_stops`, `gradient_angle`, `shadow`, and `glow`
style fields when measured. A progress bar with a visible knob uses
`payload.marker: true`. Do not wrap plain source content in an inferred card.

Every critical node must have at least one matching `evidence_refs` id. Keep
high-confidence OCR text exact, including punctuation, units, decimals, and
percent signs. Set `confidence` below 0.80 only when the ambiguity is real;
the runtime will route that proposal to review. Never invent text, numbers,
charts, citations, or decorative panels that are not visible in the source.

Before returning, check that all high-confidence OCR lines are covered by a
semantic text/data node, all boxes stay within the canvas, and no critical
text/data is covered by a raster node. Do not include Markdown, prose, code
fences, comments, or unknown JSON fields. When the request reports
`degradation.active` or `ocr.zero_detections`, inspect `canonical.png`
directly, preserve every visible critical text/data item, and treat text
completeness as requiring manual/model review. Never infer that zero OCR
means the source contains no text, and never skip ingest review reasons.

After ingest, initialize the Block gate from the user-approved blueprint.
Build only the active Block, render its slice diff and cumulative preview, and
wait for explicit user confirmation before `block-approve`. Never produce a
full-slide final build while any Block remains unapproved.

## Self-check before pass 2

After `scene.proposed.json` validates, run
`pptrestore preview <case> <case>/scene.proposed.json`. It compiles and renders
the proposal without ingesting it and writes `previews/<hash>/side_by_side.png`
(source | render), `diff.png` (red where they differ), zoomed
`regions/region_*.png` crops and `preview.json` (metrics, worst grid cells with
the nodes painted there, cells whose source detail is missing from the render,
and per-node source/render mean colours). Look at the images, fix the biggest
visible gaps in the scene (missing plates, ribbons and decorations, wrong fills
or gradients, misplaced boxes, text that wraps or shrinks differently) and
preview again, about three rounds. Preview never changes case state, and pixels
only show where the render differs: re-read canonical.png before changing copy.
