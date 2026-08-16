---
specId: TASKS-FEAT-PPT-002-001
type: tasks
parent_spec: spec.md
title: FEAT-PPT-002 任务拆解与执行跟踪表
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 已完成
confirmed: true
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, plan.md, eval.md]
---

# TASKS-FEAT-PPT-002-001 ｜ 任务拆解与执行跟踪

## 任务执行清单

- [x] **T-01 规范与 PRD 确认**: 完成根因分析与三层解耦 PRD 评审
- [x] **T-02 纯净 3D 底座与艺术浮层构建**: 生成 `assets/slide1_3d_clean_base.png` 与 `assets/slide1_poju_transparent.png`
- [x] **T-03 Slide 01 脚本三层重构**: 重构 `slides/build_slide_01.py`（3D底座 + 原生白卡片 + 镜像对齐 + 金句双翼）
- [x] **T-04 Slide 02 脚本验证**: 确认 `slides/build_slide_02.py`（拟物板夹 + 发光进度条 + KPI卡片）
- [x] **T-05 终版文稿合并与结构自检**: 合并生成 `output/presentation_IMG_7410.pptx` 并运行 structural inspection
- [x] **T-06 AGENTS.md 规则固化与 SDD 归档**: 更新 `AGENTS.md` 并完成评测回填
