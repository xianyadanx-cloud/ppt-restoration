---
specId: SPEC-FEAT-PPT-003-001
type: spec
title: 需求规格说明书 (PRD): Python 确定性视觉量化探针与 100% 纯矢量几何渲染引擎深度集成
domain: 演示文稿/文档生成/AI Agent 体系
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 待评审
confirmed: false
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [plan.md, tasks.md, eval.md]
---

# SPEC-FEAT-PPT-003-001 ｜ Python 确定性视觉量化探针与 100% 纯矢量几何渲染引擎深度集成

## 1. 业务背景与问题根因 (Background & Root Causes)

在此前的 PPT 高保真还原任务中，AI Agent 在处理复杂 3D 空间透视、拟物光影及图文排版时，存在两个核心瓶颈：
1. **多模态大模型的“空间与色彩幻觉”**：大模型（Vision LLM）擅长宏观语义理解与版式规划，但在提取绝对像素坐标、颜色 Hex 值、微小渐变及字符物理字阶时，由于图像分块（Tokenization）机制的限制，无法进行精确的确定性测量，容易产生 20~90px 的系统性坐标漂移与色彩塑料感。
2. **截屏外围系统留白的干扰**：用户上传的输入图片往往是包含操作系统桌面背景/窗口灰边的截屏，直接按原图分辨率计算坐标会导致所有幻灯片元素被整体下压与比例畸变。
3. **工具链能力的缺失**：初始 Agent 仅支持平面的矩形/圆角矩形，缺乏自由多边形（Freeform Polygon）和旋转（Rotation）支持，导致遇到 3D 透视书本时本能地将其降维为 2D 矩形。

---

## 2. 特性目标与核心定位 (Feature Objectives)

本特性旨在将 **Python 确定性视觉量化探针** 与 **100% 纯原生矢量几何渲染引擎** 深度集成进 Agent 的 SOP 规范与工具库中，形成 **「LLM 语义大脑 + Python 游标卡尺/比色计」** 的双擎协作架构：

1. **确定性画布校准 (Deterministic Canvas Calibration)**：自动识别并裁剪截图外围灰边，建立真实 16:9 画布归一化坐标系。
2. **确定性色彩与字阶采样 (Deterministic Colorimeter & Typography Probe)**：通过 Python 脚本实现像素级 RGB 比色、渐变起点/终点提取，以及根据公式 $\text{pt} = \text{height\_px} \times 0.667$ 精确计算字号。
3. **100% 纯原生矢量 3D 几何拼装 (100% Pure Vector Architecture - Zero Images)**：支持 Freeform 自由多边形、线性渐变填充、形状与文本框任意角度旋转（$\pm 7.0^\circ$），实现全 Deck 零位图、100% 原生可编辑。
4. **视觉闭环 Visual Diff 验证 (Visual Loopback QA)**：生成矢量图元仿真渲染图，自动与原图进行像素级比对，驱动坐标与排版自适应收敛。

---

## 3. 用户故事与功能验收标准 (User Stories & Acceptance Criteria)

### US-01: 自动屏幕画布探测与校准 (Auto Canvas Calibrator)
- **描述**：作为 Agent，在处理输入图片时，需自动探测图片是否存在系统灰边或外围留白，并自动校准出纯净 16:9 画布。
- **验收标准**：
  - [x] 能自动提取真实幻灯片有效视口 `(Left, Top, Right, Bottom)`；
  - [x] 所有元素坐标基于真实画布的 0-1000 归一化空间映射，消除由于系统外框引起的系统性偏移。

### US-02: 确定性比色探针与渐变色谱提取 (Deterministic Colorimeter & Gradient Probe)
- **描述**：作为 Agent，不再依靠大模型猜测 Hex 颜色，而是通过探针直接读取真实像素值。
- **验收标准**：
  - [x] 精准采样主色、辅助色、背景色、文字色及指标高亮色（如预警红 `#E11D48`、成功绿 `#16A34A`）；
  - [x] 采样 3D 顶板受光面与阴影面的线性渐变起点与终点颜色。

### US-03: 字符像素高度到 PPT 物理字阶换算 (Typography Calibrator)
- **描述**：作为 Agent，根据文字字符的像素高度，使用确定性数学公式换算出 PowerPoint 磅值。
- **验收标准**：
  - [x] 主标题（28pt）、中缝书法（34pt）、3D 标牌（24pt/12pt）、卡片正文（10.5pt）、药丸标签（10pt）均具备数学换算依据，字阶主次对比鲜明（2:1 黄金比例）。

### US-04: 100% 纯原生矢量几何与旋转拼装 (Pure Vector & Rotation Engine)
- **描述**：作为 Agent，使用 `builder.add_polygon(...)` 与 `rotation` 参数构建 3D 透视书本、活页环、光球及倾斜标牌。
- **验收标准**：
  - [x] 生成的 `.pptx` 文件中 `PICTURE`（图片）数量必须为 0；
  - [x] 3D 顶板、正面开页、书脊厚度由 Freeform 多边形拼装；
  - [x] 顶部标牌与次级横幅支持倾斜角度贴合（$\pm 7.0^\circ$）；
  - [x] 全页面所有文本、卡片、形状在 PowerPoint 中可任意双击编辑、改色、调整大小。

### US-05: 视觉闭环自检与比对 (Visual Loopback QA Gate)
- **描述**：作为 Agent，构建完成后需调用渲染与比对工具生成 Visual Diff 比对图，确保与真实画布无缝吻合。
- **验收标准**：
  - [x] 自动输出 `output/iteration_diff.png` 左右对比图；
  - [x] 通过 Gate 1 ~ Gate 4 全部门禁。

---

## 4. 质量门禁标准 (The 4 Mandatory Quality Gates)

| 门禁 | 名称 | 核心检验项 | 判定标准 |
| :--- | :--- | :--- | :--- |
| **Gate 1** | 画布与色阶门禁 | 画布校准、RGB 采样 | 消除截图灰边；提取确定性 Hex 与渐变参数 |
| **Gate 2** | 宏观蓝图门禁 | 0-1000 栅格与透视倾角 | 规划 Freeform 多边形顶点坐标与 $\pm 7.0^\circ$ 旋转角度 |
| **Gate 3** | 纯矢量几何门禁 | 0 位图图片、原生组件 | `PICTURE` 数量 = 0；6 组卡片、双层活页环、渐变光球全原生 |
| **Gate 4** | 视觉闭环门禁 | Visual Diff 像素级比对 | 生成对比图，检查文字无重影、卡片无溢出、透视贴合 |

---

## 5. 待评审事项与确认 (Pending Review)

请您审阅此 PRD，确认是否涵盖了本次优化的所有关键需求。确认后我们将推进架构设计（`plan.md`）并完成工程代码与 SOP 规范的正式同步。

## 9. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
