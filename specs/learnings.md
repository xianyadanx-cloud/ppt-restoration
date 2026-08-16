---
specId: "SPEC-FEAT-PPT-009"
title: "复盘与经验沉淀 (Learnings): 纵向流式均分与空间空洞防御"
version: "1.0"
status: "已固化"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 复盘与经验沉淀 (Learnings)

### [L-01] 质检断言的双向性：不仅防溢出 (Overflow)，更要防塌陷空洞 (Underflow)
* **核心教训**：过去质检仪只关注 `max_bottom <= 930`，导致大模型即使把所有内容挤在上半截、下半截留下 260px 巨大空洞，质检仪也会给绿灯。
* **工程对策**：增加 `Rule 6: GIANT_VOID_GAP`，断言相邻模块垂直间隙不得超过 70px，一旦出现大面积空洞立刻阻断并报出具体空隙。

### [L-02] 纵向弹性均分算子 `distribute_vertical_sections` 的必要性
* **核心教训**：局部累加计算必将导致纵向排版塌陷。
* **工程对策**：在 `spacing_grid` 中实现全局高度均分算子，强制由算法根据总高度和子项数推导段落高与间隙。
