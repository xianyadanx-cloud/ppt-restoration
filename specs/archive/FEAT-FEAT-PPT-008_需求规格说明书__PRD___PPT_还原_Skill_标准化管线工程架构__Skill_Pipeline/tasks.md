---
specId: "SPEC-FEAT-PPT-008"
title: "任务执行清单 (Tasks): PPT 还原 Skill 标准化管线工程架构"
version: "1.0"
status: "已完成"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 任务执行清单 (Tasks)

| 任务编号 | 阶段与任务目标 | 核心输出物 | Verify 验证命令 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | 创建 `skills/element_profiler/`：实现基于轮廓与圆度的形状分类器与取色引擎 | `skills/element_profiler/` | `python skills/element_profiler/profiler.py --help` | `[x]` |
| **T-02** | 创建 `skills/spacing_grid/`：实现 0-1000 栅格划分、间距与基准线计算器 | `skills/spacing_grid/` | `python skills/spacing_grid/grid_calculator.py --help` | `[x]` |
| **T-03** | 创建 `skills/vector_builder/`：实现 Manifest 到 `SlideBuilder` 原生代码映射器 | `skills/vector_builder/` | `python skills/vector_builder/code_generator.py --help` | `[x]` |
| **T-04** | 创建 `skills/layout_auditor/`：实现静态几何对齐与 DOM PICTURE=0 质检器 | `skills/layout_auditor/` | `python skills/layout_auditor/auditor.py --help` | `[x]` |
| **T-05** | 在 `tests/test_workspace.py` 中增加对 4 大 Skill 的单元测试覆盖并跑通回归套件 | `tests/test_workspace.py` | `python -m unittest tests/test_workspace.py` (13/13 通过) | `[x]` |
| **T-06** | 回填 `specs/eval.md` 和 `specs/learnings.md`，提交至本地分支 | `specs/` | `git status` | `[x]` |
