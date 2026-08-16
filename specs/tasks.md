---
specId: "SPEC-FEAT-PPT-007"
title: "任务执行清单 (Tasks): PPT 布局几何质检引擎与基准线自愈"
version: "1.0"
status: "已完成"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 任务执行清单 (Tasks)

| 任务编号 | 阶段与任务目标 | 核心输出物 | Verify 验证命令 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | 开发独立排版几何质检引擎 `tools/layout_linter.py` (双栏基准线/留白/字阶/行内居中) | `tools/layout_linter.py` | `python tools/layout_linter.py output/slide_02.pptx` | `[x]` |
| **T-02** | 精修 `slides/build_slide_02.py`：锁齐左右两栏顶底基准线、压缩字阶、调整 KPI 间隙 | `slides/build_slide_02.py` | `python slides/build_slide_02.py -o output/slide_02.pptx` | `[x]` |
| **T-03** | 运行 `tools/layout_linter.py` 对 `output/slide_02.pptx` 进行全量规则静态检查 | `output/slide_02.pptx` | `python tools/layout_linter.py output/slide_02.pptx` (全绿灯) | `[x]` |
| **T-04** | 扩展 `tests/test_workspace.py` 覆盖 Layout Linter 单测并验证全套套件 | `tests/test_workspace.py` | `python -m unittest tests/test_workspace.py` (12/12 通过) | `[x]` |
| **T-05** | 回填 `specs/eval.md` 和 `specs/learnings.md`，提交至本地分支 | `specs/` | `git status` | `[x]` |
