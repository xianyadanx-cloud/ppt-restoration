---
specId: PLAN-FEAT-PPT-002-001
type: plan
parent_spec: spec.md
title: Agent架构分层解耦与高保真3D视觉还原引擎优化技术设计
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 已评审
confirmed: true
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, eval.md, tasks.md]
---

# PLAN-FEAT-PPT-002-001 ｜ 技术方案与三层解耦架构设计

## 1. 三层解耦渲染架构 (Tri-Layer Rendering Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: 100% 原生可编辑业务层 (Native Editable Layer)       │
│  - 6 组原生白底圆角矩形卡片 (box: [142, 420, 335, 115]等)   │
│  - 镜像对齐: 左侧 align="left", 右侧 align="right"          │
│  - 文本高亮: 数据指标独立着色 (bold/color)                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: 独立艺术与光效浮层 (Artistic Motif Layer)          │
│  - assets/slide1_poju_transparent.png                       │
│  - box: [426, 150, 148, 112]                                │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: 纯净 3D 空间透视基座层 (Visual Artwork Layer)       │
│  - assets/slide1_3d_clean_base.png                          │
│  - box: [120, 200, 760, 680]                                │
│  - 0-1000 栅格标准化，纯净无业务文字                         │
└─────────────────────────────────────────────────────────────┘
```

## 2. 空间栅格与坐标定义 (Normalized 0-1000 Box Matrix)

### Slide 01:
- **Header Block**: `[60, 35, 600, 48]`
- **Quote Ribbon**: `[95, 105, 810, 50]` + Left Wing `[65, 126, 40, 8]` + Right Wing `[895, 126, 40, 8]`
- **3D Base Container**: `[120, 200, 760, 680]`
- **Poju Art**: `[426, 150, 148, 112]`
- **Left Cards (x: 142, w: 335, h: 115)**:
  - Card 1: `y=420`, Badge `[125, 408, 120, 28]` (渠道管理粗放)
  - Card 2: `y=555`, Badge `[125, 543, 120, 28]` (客户分层模糊)
  - Card 3: `y=690`, Badge `[125, 678, 120, 28]` (竞品响应滞后)
- **Right Cards (x: 522, w: 335, h: 115)**:
  - Card 1: `y=420`, Badge `[735, 408, 130, 28]` (渠道网格化精耕)
  - Card 2: `y=555`, Badge `[735, 543, 130, 28]` (客户价值分级)
  - Card 3: `y=690`, Badge `[735, 678, 130, 28]` (竞品监测反制)

## 3. 不改清单（硬约束）
- **严禁将业务正文做成图片贴入**。
- **坐标系统严格锁定在 0-1000 归一化系统内**。
- **所有数据指标必须 100% 原生可二次编辑**。
