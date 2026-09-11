# SceneSpec v2 pipeline

The runtime accepts images and individual PDF pages. It never invokes a model. The host reads canonical.png, prepares a SceneSpec proposal and independently audits its content.

## Case protocol

| Artifact | Owner / purpose |
| --- | --- |
| source/, canonical.png, registration.json, case.json | prepare: registered input and provenance |
| evidence.json | OCR, palette, guides and diagnostic layout evidence |
| agent_request.json, scene_spec_v2.md | Host handoff, supported fields and output paths |
| scene.proposed.json | Host pass 1, semantic geometry and content |
| content_audit.proposed.json | Host pass 2, independent content review |
| scene.json, content_inventory.json | Validated ingest output |
| block_gate.json | User-confirmed blueprint and sequential approvals |
| render_plan.json, builds/ | Compiler plan and content-addressed manifests |
| reviews/, reports/, renders/ | Hash-bound verification evidence |
| candidates/ | Optimization proposals awaiting audit |
| deliverables/ | Builds suggested by next |

Keep these files together in the case directory. They are runtime data, not repository assets. Removing audit or build evidence before completion invalidates approval.

## Coordinates and editability

The host uses bbox_norm [L,T,W,H] in 0–1000 coordinates. Ingest converts once to canonical pixels. Every critical node carries a block_id and evidence_refs. Native semantic kinds include text, shape, line, table, chart, badge, KPI, process and progress bar.

hybrid_editable permits raster decoration but requires native business content. strict_native permits no picture objects. OCR is a cross-check; blank OCR requires direct source inspection.

## Approval flow

prepare → host scene and independent audit → ingest → blueprint → user confirms → block-init → next → build → review → user confirms → block-approve.

Repeat build/review/approval per block. Full assembly is blocked until every block is approved. next returns executable command arrays and current status. Do not reuse stale reports after changing a scene, image or PPTX.

revise creates a proposal restricted to the active block. optimize searches bounded numeric changes using a real-renderer probe and fixed reference regions; it does not approve or ingest candidates. Every candidate needs a fresh content audit.

ingest requires a second-pass audit by default. The explicit --allow-missing-audit escape hatch remains for controlled unaudited v2 experiments; it records MISSING_COMPATIBILITY and must not be described as fully audited acceptance. It does not enable v1 scenes.

## Verification

build and verify reconcile critical text/table content against the PPT DOM. This proves preservation of the submitted scene, not correctness of image recognition.

Only a hash-bound PowerPoint render passing all gates can produce PASS. WPS and LibreOffice can produce PREVERIFIED. Missing renderers are failures, and unsupported capabilities remain explicit. Use --wps-pdf to supply a manually exported WPS PDF.

## Command reference

Run pptrestore --help, or pptrestore COMMAND --help. Commands are prepare, canonicalize, ingest, blueprint, block-init, block-status, next, build, render, review, block-approve, revise, optimize, verify, pipeline, doctor, render-probe and font-candidates.

pipeline initially returns AWAITING_MULTIMODAL_SCENE_AND_AUDIT. Resume only after supplying artifacts, ingesting, and completing mandatory block checkpoints. It is not an unattended image-recognition command.
