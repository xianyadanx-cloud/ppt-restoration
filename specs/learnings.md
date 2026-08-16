---
specId: "SPEC-FEAT-PPT-007"
title: "复盘与经验沉淀 (Learnings): 静态排版 Linter 与几何基准线"
version: "1.0"
status: "已固化"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 复盘与经验沉淀 (Learnings)

### [L-01] 彻底告别肉眼找茬：引入确定性 Layout Linter 规则断言
* **现象/问题**：为什么自动化质检以前抓不出 10px 错位？
* **根本原因**：DOM 检查只查合规（`PICTURE=0`），SSIM 全局平均掩盖了局部微观位移，导致质检失明。
* **工程对策**：开发 `tools/layout_linter.py`，直接在 DOM 树上断言多栏对齐（`abs(top1-top2)<=2`）、底部留白（`max_bottom<=930`）和字阶范围，任何微观错位直接红灯报错阻断交付。

### [L-02] 双栏排版的“全局基准线 (Baseline Grid)”优先原则
* **现象/问题**：左右两栏由不同模块编写时，容易各自给出不同的 `top` 和 `height`，产生 10px 阶梯差。
* **工程对策**：在页面级定义严格的全局空间锚点（如 `top: 315, height: 605, bottom: 920`），左右容器强制继承该基准线。
