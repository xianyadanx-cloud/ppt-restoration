# Architecture

The host agent interprets the source image and returns SceneSpec v2 plus a separate content audit. The deterministic runtime validates, compiles, renders and checks these artifacts.

| Package | Responsibility |
| --- | --- |
| contracts | SceneSpec, render operations, case and registration types |
| pipeline | prepare, ingest, blocks, blueprint, revisions and next-step guidance |
| rendering | Native primitives, semantic compiler, geometry, fonts and Office adapters |
| quality | Audits, content inventory, DOM, metrics, review and optimization |
| platform | I/O, provenance, environment checks, OCR and pixel evidence |
| cli | Parsing, shared services and individual command handlers |
| resources | Installed host prompt and Swift OCR adapter |

Contracts are independent of runtime services. CLI handlers compose services and backends. Native drawing primitives do not read cases or approvals. Renderers report capabilities and provenance; quality gates decide acceptance.

The public surface is the CLI and versioned JSON contract. Internal Python paths may change. SceneIR v1 and the historical SlideBuilder API are unsupported.

Runtime resources live inside the installed package. prepare copies its prompt into the case. The case owns sources, intermediate files, review images and deliverables. Hash-bound audit records must remain until acceptance finishes and are not committed to the repository.
