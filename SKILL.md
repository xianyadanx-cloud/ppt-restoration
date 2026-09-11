---
name: image-to-ppt
description: Restore a slide image or PDF page into editable PowerPoint with SceneSpec v2, two-pass auditing and interactive block review.
---

# Image to PPT

Read [AGENTS.md](AGENTS.md). Install the package using [README.md](README.md).

1. Run `pptrestore prepare <input> --case-dir <case> --ocr auto`.
2. Read agent_request.json, canonical.png, evidence.json and the exported scene_spec_v2.md. Return scene.proposed.json, then independently re-read the image and return content_audit.proposed.json.
3. Run `pptrestore ingest <case> <proposal> --content-audit <audit>`. Resolve NEEDS_REVIEW reasons.
4. Run blueprint, show the map and block table, wait for user confirmation, then block-init with the returned blueprint.
5. Follow next, build the active block and run review. Present local diff and cumulative preview.
6. After explicit approval, run block-approve with the current report and --user-confirmed. Repeat for remaining blocks.
7. Build and verify the full slide, deliver the PPTX and comparison with the actual verification level.

The runtime never calls a model. Empty OCR does not prove absent text. Do not use the missing-audit compatibility flag for normal restoration or manufacture approval.

Keep artifacts in the requested case directory. Use revise for active-block changes and optimize for numeric refinement; proposals require a fresh audit and ingest. See [PIPELINE.md](docs/PIPELINE.md).
