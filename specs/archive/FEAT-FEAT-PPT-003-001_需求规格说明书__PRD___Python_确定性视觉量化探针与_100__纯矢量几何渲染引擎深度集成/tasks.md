---
specId: TASKS-FEAT-PPT-003-001
type: tasks
parent_spec: spec.md
title: FEAT-PPT-003 任务拆解与执行跟踪表
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 已完成
confirmed: true
version: 1.1
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, plan.md, eval.md, learnings.md]
---

# TASKS-FEAT-PPT-003-001 ｜ 任务拆解与执行跟踪

## 任务拆解清单

- [x] **T-01 PRD 与技术设计固化**: 完善 `specs/spec.md` 与 `specs/plan.md`，确立 100% 纯原生矢量渲染与视觉闭环标准。
- [x] **T-02 视觉特征提取探针固化**: 完善 `tools/extract_visual_features.py` 与 `tools/inspect_layout_02.py`（自动画布裁切、RGB比色、字阶物理换算）。
- [x] **T-03 PPTX Helper 纯矢量与组件能力增强**: 
  - `add_polygon` 自由多边形与多角度旋转
  - `add_badge` 支持实体/渐变填充及自定义边框 (`border_color`, `border_width_pt`)
  - `add_table` 支持自定义隔行斑马纹与单行背景 (`row_bg_colors`)
  - `add_progress_bar` 支持渐变填充 (`gradient_colors`) 与珍珠发光圆环节点 (`node_glow`)
- [x] **T-04 视觉闭环渲染与对比器集成**: 固化 `tools/render_and_diff.py`，支持表格、多行富文本排版渲染与独立标题区 Visual Diff 对比。
- [x] **T-05 SOP 规范与门禁机制固化**: 更新根目录与 `agent/` 下的 `AGENTS.md`，沉淀 Slide 01/Slide 02 标准组件蓝图与代码模板。
- [x] **T-06 全量 PPTX 验收与 SDD 归档**:
  - Slide 01: `slides/build_slide_01.py` -> `output/slide_01.pptx` (PICTURE = 0, 100% Native)
  - Slide 02: `slides/build_slide_02.py` -> `output/slide_02.pptx` (PICTURE = 0, 100% Native)
  - 全部通过 Gate 1 ~ Gate 4 质量门禁。

## 变更记录
| 日期 | 变更说明 | 责任人 |
| :--- | :--- | :--- |
| **2026-08-16** | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 单元测试同步校验 | Agent/Human |
