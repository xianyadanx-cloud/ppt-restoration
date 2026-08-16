---
specId: "SPEC-FEAT-PPT-006"
title: "复盘与经验沉淀 (Learnings): Multi-Agent 编排与自动化质检"
version: "1.0"
status: "已固化"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 复盘与经验沉淀 (Learnings)

### [L-01] 架构解耦：从“单点过载”转向“工件驱动的多 Agent 网络”
* **现象/问题**：单 Agent 承担从宏观感知、写代码到视觉审核全链路，上下文冗长导致指令遗忘。
* **工程对策**：拆分为 `Architect`、`Developer`、`Reviewer`，以 `blueprint.json` 和 `review_report.json` 为数据契约，Developer 在纯净短上下文中单块生成，降低 Token 消耗并提升代码健壮性。

### [L-02] 自动化质检分流（80% 自动化 + 20% 人工把关）
* **现象/问题**：每一步都需要人工看图，用户疲劳度高。
* **工程对策**：引入 `eval_metrics.py` 自动计算 SSIM、MSE 与 DOM `PICTURE=0` 校验，自动驱动 3 轮内自愈；仅在宏观蓝图（Gate 2）与终验（Gate 4）打扰人类。
