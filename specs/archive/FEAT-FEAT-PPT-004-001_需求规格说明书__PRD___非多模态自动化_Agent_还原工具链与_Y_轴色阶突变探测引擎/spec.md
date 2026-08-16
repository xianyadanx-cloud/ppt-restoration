---
specId: "SPEC-FEAT-PPT-004-001"
title: "需求规格说明书 (PRD): 非多模态自动化 Agent 还原工具链与 Y 轴色阶突变探测引擎"
status: "已批准"
version: "1.0"
author: "AI Coding Assistant & Feng Liu"
date: "2026-08-16"
priority: "P0"
tags: ["Agent", "Vision-Independent", "ColorProfiler", "ErrorLocalizer", "SynthCode", "Y-AxisStripDetection"]
---

# 1. 业务背景与用户价值 (Context & Value)

在 PPT 图像还原到可编辑 `.pptx` 的现有流程中，Agent 高度依赖多模态大模型的视觉直觉进行“看图猜尺寸、看图猜颜色、看图找差异”，存在两大固有缺陷：
1. **语义先验幻觉**：模型倾向于按照常见卡片模式脑补嵌套大卡（如将仅有 30px 高度的局部条形标题底色 `title_strip` 误判为包裹整个正文列表的 `full_card`）；
2. **多模态看图迭代成本高且精度有限**：缺乏像素级、确定性的数学分析工具，导致微调陷入多轮盲猜循环。

本项目旨在构建一套**100% 独立于多模态 LLM**的确定性算法工具链，提供自动化分块、K-Means 色彩/渐变探测、Y 轴背景色阶突变分析、声明式代码合成以及结构化像素误差对账闭环。

---

# 2. 用户故事与验收标准 (User Stories & Acceptance Criteria)

### US-1: Y 轴背景色阶突变自动探测 (Y-Axis Background Strip Detector)
- **As a** PPT 还原 Agent,
- **I want to** 在扫描卡片区域时，自动逐行检测背景像素的突变点,
- **So that** 能够以数据精确区分 `title_strip`（局部标题底条）、`full_card`（完整底卡）与 `plain_text_area`（纯白正文无底卡），彻底杜绝脑补加框。
- **Acceptance Criteria**:
  - [x] AC-1.1: 能够沿 Y 轴采样每行背景色，排除文字边缘像素，计算行背景有效 RGB。
  - [x] AC-1.2: 连续高度在 `15px - 55px` 且下方为纯白色的区域，自动归类为 `title_strip`。
  - [x] AC-1.3: 纯白区域自动标记为 `plain_text_area` 并附带说明 `Direct canvas/white background for body bullets`。

### US-2: 全自动颜色与渐变提取器 (Automatic Color & Gradient Profiler)
- **As a** PPT 还原 Agent,
- **I want to** 指定任意 0-1000 归一化 box 区域，自动提取主色、渐变方向及起止色,
- **So that** 无需多模态模型猜测色值与角度。
- **Acceptance Criteria**:
  - [x] AC-2.1: 采用 K-Means 聚类输出 Top-5 主色（HEX）。
  - [x] AC-2.2: 比较水平/垂直/对角线像素方差，自动输出渐变方向与两端精确色。
  - [x] AC-2.3: 采样边缘 3px 判断真实边框色与粗细。

### US-3: 声明式 JSON 到 Python 代码合成器 (JSON-to-Code Synthesizer)
- **As a** PPT 还原 Agent,
- **I want to** 将声明式 `block_spec.json` 自动编译为 `build_slide_XX.py` 脚本,
- **So that** 代码 100% 符合 `SlideBuilder` 纯矢量规范并支持 `--blocks` 与 `--cumulative-up-to` 模块化调试。
- **Acceptance Criteria**:
  - [x] AC-3.1: 映射 `card`, `gradient_card`, `badge`, `textbox`, `table`, `progress_bar` 到标准 API。
  - [x] AC-3.2: 自动生成包含主调度函数与 CLI 的完整 Python 模块。

### US-4: 结构化像素误差定位与修复器 (Error Localizer & Actionable Fix Generator)
- **As a** PPT 还原 Agent,
- **I want to** 对比 PPTX 渲染图与原图，输出结构化 JSON 修复建议,
- **So that** 能够直接根据机器指令修改代码，无需人工或大模型肉眼比对。
- **Acceptance Criteria**:
  - [x] AC-4.1: 输出每项元素的 $\Delta E$ 色差、严重等级（`CRITICAL` / `HIGH` / `MEDIUM`）。
  - [x] AC-4.2: 提供可直接执行的代码修复片段（如 `bg_color="..."`, `font_color="..."`）。

## 9. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
