---
specId: LEARNINGS-FEAT-PPT-002-001
type: learnings
parent_spec: spec.md
title: FEAT-PPT-002 架构复盘与最佳工程实践
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 沉淀完成
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
---

# LEARNINGS-FEAT-PPT-002-001 ｜ 架构复盘与最佳工程实践

## 1. 核心工程洞察：三层解耦渲染架构 (Tri-Layer Decoupling)
- **教训**：当幻灯片中存在复杂 3D 空间透视、厚度挤压、阴影投影时，PowerPoint 原生图形引擎（python-pptx）无法原生绘制自由三维多边形。如果 Agent 机械死板地追求“全部纯代码绘制”，就会把原本精美的 3D 折叠书本降维成两个丑陋的 2D 扁平大色块。
- **正解**：采用 **三层解耦（Tri-Layer）架构**：
  1. **Layer 1 (纯净 3D 基座层)**：提取/生成纯净无业务文字（Zero Text）的 3D 几何基座，保留 100% 空间视觉冲击力。
  2. **Layer 2 (艺术浮层)**：书法毛笔字、3D 渐变光球等作为独立透明资产居中浮动。
  3. **Layer 3 (100% 原生可编辑业务层)**：所有业务卡片容器、药丸标签、正文、数字指标 100% 采用 PPT 原生文本框与矢量形状精准吸附在底座上。

## 2. 空间栅格与留白（呼吸感）原则
- 咨询级 PPT 的高级感很大程度上来源于克制且充裕的留白。
- 绝不能将卡片无休止拉伸铺满全屏。垂直高度约束在 60%~70% 范围内，四周保留 15%~20% 呼吸空间，能让画面视觉重心更加聚焦稳定。
