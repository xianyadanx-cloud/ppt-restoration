---
specId: "SPEC-FEAT-PPT-009"
title: "任务执行清单 (Tasks): 纵向弹性均分算子与空洞质检断言"
version: "1.0"
status: "已完成"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 任务执行清单 (Tasks)

| 任务编号 | 阶段与任务目标 | 核心输出物 | Verify 验证命令 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | 在 `skills/spacing_grid/grid_calculator.py` 中实现 `distribute_vertical_sections` 纵向均分算子 | `skills/spacing_grid/` | `python -m unittest tests/test_workspace.py -k test_vertical_flex_and_void_gap_audit` | `[x]` |
| **T-02** | 在 `tools/layout_linter.py` 与 `skills/layout_auditor/` 中新增 `Rule 6` 容器留白空洞断言 | `tools/layout_linter.py` | `python tools/layout_linter.py output/slide_02.pptx` | `[x]` |
| **T-03** | 重构 `slides/build_slide_02.py` 的 Block 5，消除 261px 惨白空白，实现饱满舒展排版 | `slides/build_slide_02.py` | `python slides/build_slide_02.py -o output/slide_02.pptx` | `[x]` |
| **T-04** | 在 `tests/test_workspace.py` 中增加纵向弹性算子与空洞断言的单测 | `tests/test_workspace.py` | `python -m unittest tests/test_workspace.py` (14/14 通过) | `[x]` |
| **T-05** | 回填 `specs/eval.md` 和 `specs/learnings.md`，提交至本地分支 | `specs/` | `git status` | `[x]` |
