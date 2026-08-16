---
specId: LEARNINGS-PPT-001
type: learnings
parent_spec: spec.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent & Human Reviewer
status: 已确认
confirmed: true
version: 1.0
updated_at: 2026-08-16
related_specs: [spec.md, plan.md, tasks.md, eval.md]
---

# LEARNINGS-PPT-001 ｜ PPT 原生还原与 SDD 实战经验复盘沉淀

## 🎯 核心认知跃迁

在本次将 `input/IMG_7410.JPG` 还原为 `output/presentation_IMG_7410.pptx` 的迭代过程中，我们严格践行了 **`zszc_ai_coding` 的 SDD（Spec-Driven Development）规范体系**。通过从初期的“死板扁平盒”到最终“3D分层高保真”的蜕变，沉淀出以下 4 条高价值工程实践：

---

### 📌 [L-01] 3D 视觉隐喻与原生可编辑性的“分层混合还原”法则
- **问题现象**：第一轮生成时，Slide 1 中极具设计感与空间透视的“3D 对开折页书本/活页夹”，被简单粗暴地降维成了两个生硬的 2D 扁平矩形框，完全丢失了原图的艺术灵魂。
- **根本原因**：陷入了教条主义的“必须用纯原生 PPT 多边形从零拼接一切”，忽略了 3D 空间透视与光影在 Office 矢量图形中的表达极限。
- **修复方案与最佳实践**：采用 **“4 层分层混合还原架构”**——将 3D 无字透视书本作为 Layer 1 容器切片底图；在其上层（Layer 2~4）严丝合缝叠加原生白底圆角卡片、切角标签与 100% 可编辑的文本框。
- **可复用性**：凡是遇到带有复杂 3D 拟态、光影底座、特定质感背景的咨询级 PPT，一律采用“3D 艺术底图 + 上层纯原生可编辑元素”的分层渲染模式。

---

### 📌 [L-02] 数据可视化的维度守恒定律（严禁图表/进度条降维为纯文字）
- **问题现象**：Slide 2 核心战役表格中的“整体完成率”，原图是带有发光节点与渐变胶囊的条形进度条，第一轮代码却退化成了枯燥的纯文字 `"84%"`。
- **根本原因**：`pptx_helper.py` 基础库缺乏细粒度的可视化微组件抽象，导致 Agent 在遇到复合图表时只能做降维妥协。
- **修复方案与最佳实践**：在 `SlideBuilder` 中封装 `add_progress_bar()`，直接生成底槽、填充胶囊、发光节点与百分比标签组合；同时封装 `add_kpi_card()` 实现三层复合指标卡。
- **可复用性**：建立原生可视化微组件库，杜绝任何图表元素向纯文字的无损妥协。

---

### 📌 [L-03] 咨询级排版的“字阶张力”与“呼吸感”控制
- **问题现象**：初版生成的卡片内各行文字字号过于接近（14pt vs 11pt），KPI 数字不够突出，卡片间距缺乏韵律。
- **根本原因**：未严格遵循咨询级排版字阶规范（如 CyberPPT 的 Typography Gate）。
- **修复方案与最佳实践**：拉大字阶反差（大标题 26pt、KPI 巨号数字 17-24pt、小胶囊 8-9pt），关键指标数字（如 `85%`、`30天内`、`低于保本线`）采用语义化红/蓝/绿高亮加粗。

---

### 📌 [L-04] SDD（Spec-Driven Development）规范驱动开发在 AI Agent 中的价值
- **总结**：通过 `spec.md`（需求消歧与 US 验收标准）-> `plan.md`（不改清单与分层架构）-> `tasks.md`（严格附带 verify 命令）-> `eval.md`（AC 矩阵与回填判定）-> `learnings.md`（复盘沉淀）的五文档闭环，彻底根治了 AI Agent 的黑盒盲目试错，使得每一次代码演进都具备高度确定性与可度量性。
