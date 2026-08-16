---
specId: "SPEC-FEAT-PPT-008"
title: "需求规格说明书 (PRD): PPT 还原 Skill 标准化管线工程架构 (Skill Pipeline)"
version: "1.0"
status: "已批准"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 需求规格说明书 (PRD): PPT 还原 Skill 标准化管线工程架构 (Skill Pipeline)

> **目标**：彻底解决还原过程中因模型概率性猜测导致的“形状看错（方块vs正圆）、色块脑补、间距漂移”等问题，将感知、度量、代码映射与质检全面 Skill 化，构建标准化的确定性工业级管线。

---

## 🎯 1. 业务价值与用户故事 (User Stories)

### [US-01] 微观元素与几何特征识别 Skill (`skills/element-profiler/`)
* **需求描述**：提供可独立运行的 Skill，输入局部切片图像，通过轮廓分析和数学度量（圆度、纵横比、K-Means 色彩、文字）输出结构化 `element_manifest.json`，严格分类形状（`SHAPE_CIRCLE`、`SHAPE_PILL`、`SHAPE_RECT_ROUNDED`、`SHAPE_RECT_SHARP`、`TEXT_PLAIN`）。
* **验收标准**：能够将 Block 5 中的序号 `1`/`2` 准确识别为 `SHAPE_CIRCLE`，标题识别为 `TEXT_PLAIN`（无背景长条）。

### [US-02] 栅格与间距度量 Skill (`skills/spacing-grid/`)
* **需求描述**：提供基于 0-1000 坐标系的栅格划分与间距计算 Skill，计算各元素绝对包围盒 `box: [L, T, W, H]`、相对间距 `gap_x`/`gap_y` 以及对齐基准线。
* **验收标准**：输出包含精确坐标与对齐关系的布局描述工件。

### [US-03] 纯矢量代码生成 Skill (`skills/vector-builder/`)
* **需求描述**：接收 `manifest.json`，按照 1:1 确定性规则翻译为 `SlideBuilder` 原生 Python 代码（严格遵守 `PICTURE=0`）。
* **验收标准**：根据形状类型调用对应的 `add_badge(radius=True)`、`add_card`、`add_textbox`。

### [US-04] 布局几何红线质检 Skill (`skills/layout-auditor/`)
* **需求描述**：自动化检查双栏对齐（`top_delta <= 2`）、底部留白（`max_bottom <= 930`）、字阶合规性与 DOM PICTURE 计数。
* **验收标准**：违规项报错阻断，全达标输出绿灯结论。

---

## 🚫 2. 盲区确认表与不改清单 (Non-Goals)
| 事项 | 裁决状态 | 裁决依据与处理方式 |
| :--- | :--- | :--- |
| **标准 Skill 规范** | **严格遵循** | 每个 Skill 包含标准的 `SKILL.md`（定义职责、参数、输入输出工件）和执行代码。 |
| **0-1000 坐标系** | **坚决保留** | 所有 Skill 统一在 0-1000 归一化空间中传递数据。 |
| **与 Orchestrator 集成** | **深度整合** | Orchestrator 负责按流水线顺次调度 4 大 Skill 算子。 |

## 9. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
