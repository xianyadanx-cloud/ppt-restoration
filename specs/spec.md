---
specId: "SPEC-FEAT-PPT-009"
title: "需求规格说明书 (PRD): Skill 体系深度升级：纵向弹性均分算子与容器留白空洞质检断言"
version: "1.0"
status: "已批准"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 需求规格说明书 (PRD): Skill 体系深度升级：纵向弹性均分算子与容器留白空洞质检断言

> **目标**：通过在 `spacing_grid` 中引入确定性纵向弹性均分算子，并在 `layout_auditor` 中增加空洞断言规则，彻底消灭“模块挤压、下部留出 261px 巨大空白”的排版缺陷。

---

## 🎯 1. 业务价值与用户故事 (User Stories)

### [US-01] 纵向弹性均分算子 (`skills/spacing_grid/grid_calculator.py`)
* **需求描述**：提供 `distribute_vertical_sections` 算法算子，接收父容器高度 `container_h`、顶部/底部保留高度和模块数量，自动按 `space_between` 或 `space_evenly` 计算每个 Section 的 `[top, height]` 和呼吸间隙。
* **验收标准**：在 620px 高度、2 个模块下，准确计算出两个高约 165px 的区块并保留 40px 间隙。

### [US-02] 容器留白空洞与填充率质检断言 (`skills/layout_auditor/` & `tools/layout_linter.py`)
* **需求描述**：在 Linter 中新增 `Rule 6`：
  - 断言容器内相邻垂直模块的垂直间距 $\le 70\text{px}$（拦截如 261px 的空洞）；
  - 断言容器内容垂直填充率 $\ge 70\%$。
* **验收标准**：当内容严重塌陷或出现大面积空白时，Linter 准确报错 `[RULE 6: GIANT_VOID_GAP]`。

### [US-03] Block 5 空间饱满度自愈与全页回归
* **需求描述**：应用新算子重新编排 Block 5，消除 261px 空洞，并通过 Linter 全绿灯。
* **验收标准**：`layout_auditor` 全通过，`test_workspace.py` 全部单元测试通过。

## 9. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
