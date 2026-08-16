---
specId: "SPEC-FEAT-PPT-005"
title: "复盘与经验沉淀 (Learnings): 弹性布局与物理字号拟合"
version: "1.0"
status: "已固化"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 复盘与经验沉淀 (Learnings)

### [L-01] 杜绝大模型数字盲猜：从“绝对硬算”转向“流式容器”
* **现象/问题**：Agent 编写 PPT 卡片时，每次都在微调 `badge.top`、`val.top`、`label.top`，加减法容易算错导致重叠或溢出。
* **根本原因**：LLM 擅长语义装配与结构化声明，不擅长在思维链中高频进行多级空间几何算术。
* **工程对策**：封装 `add_stack`（流式堆叠）与 `add_grid`（等宽网格），让 Agent 声明结构，由 Python 算法做对齐与等间距计算。

### [L-02] 物理字符宽度测算（Typographic Metrics）防折行
* **现象/问题**：Agent 设定的字号在 PPT 渲染时常因中英文字形宽度不同被折成两行。
* **根本原因**：PPT 文本框存在默认内部 margin 与字形行高，字符数不等于物理宽度。
* **工程对策**：在 `add_textbox` 中引入 `auto_fit_font=True`，通过 `estimate_text_width_pt` 物理测算中英文真实占用宽度，并在超出可用宽度 90% 时自动降级字号，杜绝折行。

### [L-03] 固化 Design Tokens 规范池
* **现象/问题**：Agent 随意分配字号与间距，导致页面视觉阶梯混乱。
* **工程对策**：在 `pptx_helper` 建立 `Tokens` 常量类，在 Prompt 和代码中限制 Agent 统一使用标准字阶（32/24/22/16/14/11/8.5pt）。
