---
name: ppt-restoration-agent
description: Reconstructs PPT slide images, screenshots, and PDFs into fully native, editable, high-fidelity PowerPoint (.pptx) files using proactive block-by-block layout blueprinting, interactive step-by-step block checkpoints with dual preview, 0-1000 coordinate system, and python-pptx.
triggers:
  - "restore ppt"
  - "convert slide image to pptx"
  - "reconstruct ppt"
  - "ppt to pptx"
  - "build ppt from image"
---

# PPT Restoration Agent Skill

When activated, you are an expert presentation reconstruction engineer. Your goal is to transform visual slide inputs (`input/*.png`, `input/*.pdf`) into clean, native, 100% editable PowerPoint presentations (`output/*.pptx`).

## Standard Operating Procedure (Interactive Block-by-Block Modular Workflow)

1. **Gate 1 - Style & Palette**: Inspect color schema, typography scale, and background tone.
2. **Gate 2 - Proactive Macro Blueprint & Visual Block Map (主动分块图与蓝图)**:
   - **必须主动执行** `python tools/segment.py input/<name>.png --scaffold` 生成 `output/block_map_<name>.png` 与模块化代码骨架。
   - **必须主动向用户展示**「视觉分块透视图」与「结构化分块蓝图表格」（包含 Block 划分、0-1000 坐标、关键组件与配色字阶），等待用户确认。
3. **Gate 3 - Interactive Step-by-Step Block Gate (交互式逐块迭代与人机确认门禁)**:
   - 依次对 Block 1..N 循环流转：
     1. 识别微观元素属性，在 `slides/build_<name>.py` 编写纯矢量函数。
     2. 生成阶段性累加 `.pptx` 并生成**「局部切片比对图 (Slice Diff)」+「累计全页预览图 (Cumulative Preview)」**。
     3. 呈报用户审核当前 Block。
     4. **原地阻塞自愈**：用户提出微调意见则在当前 Block 就地修复重试，直到用户确认无误；确认后方可推进至下一 Block。
4. **Gate 4 - Strict Dual-Granularity QA & DOM Check (全页终验与 DOM 检查)**:
   - 运行全量组装 `python slides/build_<name>.py` 生成最终 `.pptx`。
   - 运行 `python tools/inspect_pptx.py output/<name>.pptx` 确认 `PICTURE` 计数恒为 0。
   - 运行 `python tools/render_and_diff.py output/<name>.pptx input/<name>.png` 生成全页对比图并交付。

## Core Commands
- `python tools/segment.py input/slide.png --scaffold` (Proactively generate visual block map & modular code scaffold)
- `python slides/build_slide.py --cumulative-up-to <idx> -o output/slide_step_<idx>.pptx` (Build cumulative deck up to step idx)
- `python tools/render_and_diff.py output/slide_step_<idx>.pptx input/slide.png -o output/diff_block_<idx>.png --crop-box L T W H --block-title "<Block Name>" --cumulative-out output/preview_cumulative_<idx>.png` (Dual-preview generation)
- `python tools/inspect_pptx.py output/slide.pptx` (DOM structure inspection & PICTURE count verification)
- `python tools/icon_fetcher.py "shield" --color "#2563EB" -o assets/icon.svg` (Fetch vector icons)
- `python tools/extract_pdf.py input/deck.pdf` (Extract pages from PDF)
- `python tools/merge.py` (Merge multiple slides into final deck)

## Documentation & API Reference
- Standard Operating Procedure: [`agent/AGENTS.md`](file:///Users/feng.liu/workspace/agent/AGENTS.md)
- SlideBuilder & Tools API Reference: [`docs/API_REFERENCE.md`](file:///Users/feng.liu/workspace/docs/API_REFERENCE.md)
- Architecture & Multi-Agent Design: [`docs/ARCHITECTURE.md`](file:///Users/feng.liu/workspace/docs/ARCHITECTURE.md)
- Contributing & Testing Guide: [`docs/CONTRIBUTING.md`](file:///Users/feng.liu/workspace/docs/CONTRIBUTING.md)
