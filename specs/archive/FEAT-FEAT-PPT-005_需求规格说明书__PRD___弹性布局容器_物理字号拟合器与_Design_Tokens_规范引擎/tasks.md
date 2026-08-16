---
specId: "SPEC-FEAT-PPT-005"
title: "任务执行清单 (Tasks): 弹性布局容器与物理字号拟合引擎"
version: "1.0"
status: "已完成"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 任务执行清单 (Tasks)

| 任务编号 | 阶段与任务目标 | 核心输出物 | Verify 验证命令 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | 实现 `estimate_text_width_pt` 与 `auto_fit_font` 字符测算与防溢出算法 | `tools/pptx_helper.py` | `python -m unittest tests/test_workspace.py` | `[x]` |
| **T-02** | 实现 `DesignTokens` 常量规范池（字阶/间距/圆角/层级） | `tools/pptx_helper.py` | `python -m unittest tests/test_workspace.py` | `[x]` |
| **T-03** | 实现 `add_stack` 弹性流式堆叠布局引擎（垂直/水平流、自动居中、等间距） | `tools/pptx_helper.py` | `python -m unittest tests/test_workspace.py` | `[x]` |
| **T-04** | 实现 `add_grid` 弹性网格布局引擎（多列均分、间距分发）与 `add_flex_card` | `tools/pptx_helper.py` | `python -m unittest tests/test_workspace.py` | `[x]` |
| **T-05** | 编写扩展单元测试套件，全面覆盖 US-01~US-04 验收标准 | `tests/test_workspace.py` | `python -m unittest tests/test_workspace.py` (9/9 通过) | `[x]` |
| **T-06** | 同步更新 `docs/API_REFERENCE.md` 并回填 `specs/eval.md` & `specs/learnings.md` | `docs/API_REFERENCE.md`, `specs/` | `git status` | `[x]` |
