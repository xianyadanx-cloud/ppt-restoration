---
specId: PLAN-<PROJECT>-001
type: plan
parent_spec: spec.md
title: <技术架构与实现方案设计>
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: <负责人 / AI Coding Agent>
status: 草稿
confirmed: false
version: 0.1
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
related_specs: [spec.md, eval.md, tasks.md]
---

# PLAN-<PROJECT>-001 ｜ <项目名称> 技术方案与分层设计

## 1. 系统分层架构（4-Layer Rendering Pipeline）
- Layer 1: 底图与 3D 拟态透视层 (Background / Sliced Metaphor Plate)
- Layer 2: 原生矢量几何卡片层 (Native Cards, Badges, Arrows)
- Layer 3: 原生数据可视化与进度条层 (Native Tables, Charts, Progress Bars)
- Layer 4: 原生富文本层 (100% Native TextFrames, Bold Highlights)

## 2. 核心组件扩展与 API 规范
列出需要在 `tools/pptx_helper.py` 中新增或调用的核心方法签名及参数定义。

## 5. 降级与容错设计
- 切片素材缺失时的平滑回退策略。
- 渲染环境缺失（如 OfficeCLI / Keynote）时的回退验证策略。

## 6. 不改清单（硬约束，编码时绝对不能碰）
- 严禁将可读文本截图贴图。
- 空间坐标严格锁定在 0-1000 归一化系统内。
- 保持已发布的 tools 公共 API 向后兼容。

## 8. 变更记录

| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **v0.1** | 初始起草 | Agent 基于 spec.md 起草架构方案 | Coding Agent |
