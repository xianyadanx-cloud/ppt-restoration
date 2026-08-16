---
specId: "SPEC-FEAT-PPT-008"
title: "复盘与经验沉淀 (Learnings): Skill 管线与确定性算子"
version: "1.0"
status: "已固化"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 复盘与经验沉淀 (Learnings)

### [L-01] 从“概率性 Prompt”转向“确定性 Skill 算子管线”
* **核心痛点**：Prompt 无法完全约束 LLM 的概率性幻觉（例如把正圆认成方块、随意脑补长条底板）。
* **工程对策**：将还原链路拆分为 `element_profiler`（数学算圆度）、`spacing_grid`（算绝对坐标与栅格）、`vector_builder`（1:1 编译代码）、`layout_auditor`（几何断言拦截），以标准 JSON 工件连接，彻底消除人为主观臆测。
