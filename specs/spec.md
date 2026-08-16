---
specId: "SPEC-FEAT-PPT-006"
title: "需求规格说明书 (PRD): Multi-Agent 角色库、自动化质检与编排调度引擎"
version: "1.0"
status: "已批准"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 需求规格说明书 (PRD): Multi-Agent 角色库、自动化质检与编排调度引擎

> **目标**：将单 Agent 串行流程解耦为基于结构化文件协议驱动的 Multi-Agent 协作网络，大幅降低人工打扰频次（从 15 次降至 2 次），实现干净上下文代码生成与自动化视觉质检自愈。

---

## 🎯 1. 业务价值与用户故事 (User Stories)

### [US-01] 专职 Agent 角色 Prompt 规范库 (`agent/roles/`)
* **需求描述**：明确定义 3 大独立 Agent 角色的系统 Prompt 与任务契约：
  - `architect.md`：宏观感知与分块蓝图规划师（负责 Gate 1 & Gate 2，输出 `blueprint.json`）。
  - `developer.md`：单 Block 纯代码生成专家（接收单个 Block Spec 与 API 参考，输出独立的 Python Block 函数）。
  - `reviewer.md`：多模态视觉 QA 与自愈驱动专家（比对 Slice Diff，分析 DOM 结构，输出结构化 `review_report.json`）。
* **验收标准**：每个角色 Prompt 包含严密的输入/输出契约、行为边界与错误处理规范。

### [US-02] 自动化质检与度量工具 (`tools/eval_metrics.py`)
* **需求描述**：提供确定性质检工具，无需人工肉眼比对即可自动化评估局部和全局渲染质量。
* **验收标准**：
  - 计算生成图与原图的 **SSIM 结构相似度** 与 **均方误差 (MSE)**；
  - 提取 DOM 结构并严格验证 `PICTURE` 计数为 0；
  - 自动输出结构化评分报告 `review_report.json`（包含 passed 状态、ssim 评分、缺陷列表）。

### [US-03] 端到端多 Agent 任务编排调度总线 (`tools/orchestrator.py`)
* **需求描述**：实现多 Agent 的调度与状态机引擎，支持命令行一键运行：
  - 模式 1：`python tools/orchestrator.py plan input/demo.png`（调用 Architect 生成蓝图并呈报确认）。
  - 模式 2：`python tools/orchestrator.py run input/demo.png`（按拓扑顺序调度 Developer 独立编码与 Reviewer 自动化自愈，支持最大自愈次数限制）。
  - 模式 3：`python tools/orchestrator.py assemble input/demo.png`（全页组装与终验交付）。
* **验收标准**：
  - 任务状态机清晰（PLANNING -> REVIEWING_BLUEPRINT -> EXECUTING_BLOCKS -> ASSEMBLING -> DONE）；
  - 自动管理上下文隔离与产物拼装。

---

## 🚫 2. 盲区确认表与不改清单 (Non-Goals)
| 事项 | 裁决状态 | 裁决依据与处理方式 |
| :--- | :--- | :--- |
| **0-1000 坐标系** | **坚决保留** | 所有 Agent 角色与中介 JSON 必须严格遵循 0-1000 坐标系。 |
| **自愈上限熔断** | **设为 3 次** | 单 Block 自动自愈上限 3 次，防止不可解异常陷入死循环。 |
| **人机交互节点** | **保留 2 次** | 仅保留 Gate 2 蓝图确认与 Gate 4 终验，其余微观自愈由 Reviewer 接管。 |

## 9. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
