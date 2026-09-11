# Image-to-PPT Agent contract

Use SceneSpec v2. The multimodal host owns image interpretation; deterministic tools own measurement, validation, compilation and verification. Read SKILL.md and the case's agent_request.json.

## Restoration checkpoints

1. Run prepare and inspect canonical.png directly. Read evidence.json and OCR status. Empty OCR never proves that there is no text.
2. Produce scene.proposed.json with public bbox_norm [left, top, width, height] in 0–1000 coordinates. Preserve titles, body text, numbers, units, table cells, labels and footnotes. Assign every critical node a block_id and evidence_refs.
3. Re-read the image independently and produce content_audit.proposed.json. Never manufacture confidence or user approval.
4. Run ingest and resolve NEEDS_REVIEW reasons. Never overwrite validated scene.json manually.
5. Run blueprint. Show the block map and a table of IDs, boxes, components, measured colors and typography. Wait for explicit user confirmation, then block-init.
6. Follow next. Build the active block and previously approved blocks only. Run review and show the local comparison plus cumulative preview. Fix the active block until explicitly approved.
7. Run block-approve only with user confirmation and the current hash-bound REVIEW_READY report.
8. Full build is allowed only after every block is approved. Run verify and deliver the PPTX and visual comparison.

Critical business content must be native editable text, tables, charts or shapes. hybrid_editable permits decorative raster only; strict_native requires zero pictures. Preserve reference-specific geometry. Measure colors from evidence/image pixels.

PowerPoint is required for formal PASS. LibreOffice and WPS give PREVERIFIED evidence. Missing renderers, fonts or OCR must be reported accurately. Tests and DOM preservation do not prove source-image recognition or visual fidelity.

## Repository maintenance

Keep product code in src/ppt_restore, tests in tests and documentation in docs. Do not add SDD records, customer images, historical slide scripts or generated PPTX/PDF/images. Tests use temporary directories. pyproject.toml is the dependency and packaging source.

The CLI and SceneSpec v2 are the public interfaces. Internal Python paths may change. Verify non-editable wheel installation outside the checkout before shipping. Resources must not depend on checkout paths.
