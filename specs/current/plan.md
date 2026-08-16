---
specId: PLAN-AUTO-HEAL-001
type: plan
parent_spec: spec.md
title: 自动化视觉校验与自愈工具链架构设计
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 草稿
confirmed: false
version: 0.1
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, eval.md, tasks.md]
---

# PLAN-AUTO-HEAL-001 ｜ 自动化视觉校验与自愈工具链 技术方案与分层设计

## 1. 系统分层架构（Auto-Healing Pipeline）
为满足 `spec.md` 要求的精准量化与反馈，将构建分为三个独立引擎层：
- **Layer 1: 图像量化偏差分析层 (Pixel-level Delta Analysis Layer)** 
  增强 `diff_analyzer.py`，计算并生成 `SSIM`、`Error Pixel Rate` 以及像素级热力分布图（Thermal Heatmap）。
- **Layer 2: 结构化属性对比引擎 (DOM vs Image Property Diff Engine)**
  增强 `compare_properties.py`，建立参数对比矩阵，提取 PPTX 原生组件属性并与图像关键视觉特征（Bounding Box, Color HEX, Line Height）作对比。
- **Layer 3: Agent 自愈指令适配层 (Agent Self-Healing Interface Layer)**
  输出机器友好的 JSON 摘要与文字建议，使 Agent 可以直接获取修正指令（如 `[Actionable] Move block top by +12px`）。

## 2. 核心组件扩展与 API 规范
**`tools/diff_analyzer.py`**:
- `calculate_metrics_and_heatmap(img1, img2, max_delta)` 需返回：
  `metrics = {"ssim": float, "error_rate": float, "max_error_pos": (x, y)}`
- 命令行需增加 `--json` 或直接输出可读的指标块，并在生成对比图的同时保存 `heatmap.png`。

**`tools/compare_properties.py`**:
- 引入对比逻辑：读取 PPTX 的 Shape Tree，提取真实 `L, T, W, H` 和文字/颜色。将其与预配置/实测的原图参数进行对比。
- API：`def compare_shapes_with_gt(pptx_path, gt_data) -> List[DiffReport]`。

## 5. 降级与容错设计
- 如果发生极端颜色偏差导致的无效对比，通过捕获异常安全降级，退回到“人工主观打分”的备用分支。
- 保证无外部二进制库依赖，完全使用 PIL (Pillow) 纯计算实现 SSIM 近似和热力图映射。

## 6. 不改清单（硬约束，编码时绝对不能碰）
- **严禁引入重量级机器视觉库（如 OpenCV、TensorFlow）**，必须保持脚手架的轻量级与兼容性。
- 绝不能破坏现有的 `--cumulative-up-to` 和 `--block` 参数结构，必须作为向下兼容的附加模块。
- 生成的热力图和矩阵报告文件须输出到 `output/` 临时目录，严禁污染 `input/` 源码区。

## 8. 变更记录

| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **v0.1** | 初始起草 | Agent 基于 spec.md 起草架构方案与API设计 | 待用户评审 |
