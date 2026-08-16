---
specId: SPEC-AUTO-HEAL-001
type: spec
title: 自动化视觉校验与自愈闭环基础设施 (Auto-Healing Visual Diff Toolchain)
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 草稿
confirmed: false
version: 0.1
created_at: 2026-08-16
updated_at: 2026-08-16
tier: medium
related_specs: [plan.md, eval.md, tasks.md]
---

# SPEC-AUTO-HEAL-001 ｜ 自动化视觉校验与自愈闭环基础设施 需求规格说明书

## 1. 背景与目标
在多模态 Agent 尝试根据原始参考图（Ground Truth）还原 PPTX 页面时，普遍存在“**无法准确感知微观视觉差异与代码属性映射**”的痛点。现有的视觉比对仅依赖低分辨率并排双图，Agent 只能得出“看起来差不多”的定性结论，无法定位 1~2px 的位置偏差、轻微的 HEX 颜色漂移、以及字重字阶的具体差异，最终导致 Agent **无法进行自我验收与自愈**，必须依赖人工肉眼 Review。

**本次迭代目标**：
建立基于**属性差分矩阵**与**像素热力图指标**的自动化自愈工具链。使 Agent 能够：
1. 精准提取 PPTX DOM 参数与原图图像特征，形成定量比对表；
2. 提取 SSIM 和显性差异像素占比（Error Pixel Rate），作为严苛数字门禁；
3. 输出明确的误差坐标与修改指令，实现完全无人值守的自动化验收与局部自愈。

## 2. 业务语义与元语消歧（AI 必读，先于一切）

- **参数级属性比对（Parameter Diff Matrix）**：不仅比对图像差异，还需比对提取的真实物理量。例如 `font_size`（代码字号 vs 原图实测字阶高推算值）、`bg_color`（代码 HEX vs 原图色块采样HEX）。
- **显性误差像素率（Error Pixel Rate）**：两个像素间欧氏颜色距离 > 25 即视为显性差异，计算全图所有显性差异像素占比。
- **微观切片（Micro Crop）**：专门针对单个按钮、标签或进度条的二级放大裁切区域，用于验证层级、描边和圆角。

### 2.1 裁决与盲区确认表

| 序号 | 待裁决项 / 潜在盲区 | 暂定结论与处理口径 | 裁决依据 |
| :--- | :--- | :--- | :--- |
| **D-01** | **验收指标的及格线阈值**设定 | 暂定 `SSIM > 0.92` 且 `Error Pixel Rate < 5.0%` 视为全页自动通过门禁 (PASS)。 | 肉眼难以察觉的误差容忍阈值。需人工确认是否合理。 |
| **D-02** | **热力误差图谱算法边界** | 仅依赖纯 Python + PIL，不用 OpenCV 等重型视觉库，保障跨平台即插即用。 | 遵守项目“轻量级无依赖”理念，降低部署门槛。 |
| **D-03** | **属性逆向映射机制** | 比对脚本在发现像素热力偏差后，需反推输出推荐的代码修改（例如 `建议 box[1] 增加 5`）。 | Agent 本质上缺乏“观图改码”直觉，需要确定性的数值调整。 |

## 3. 范围与场景（Scope）
- **In Scope**：
  - 升级 `tools/compare_properties.py` 输出结构化属性偏差矩阵。
  - 升级 `tools/diff_analyzer.py` 支持量化指标门禁与热力图标注。
  - 输出机器可读的 JSON 结构，用于对接后续 Agent 的自愈 Prompt State Machine。
- **Out of Scope**：
  - 新增任何基于大模型权重的视觉识别接口（仍保持工具链纯算法比对）。

## 5. 验收标准（Acceptance Criteria）

- **[US-01] 属性量化差异矩阵提取**
  工具能接收指定切片，自动分析输出原图实测颜色/尺寸与 PPTX 的具体参数差异表。
- **[US-02] 像素级误差热力图与数字化门禁**
  工具运行后能够稳定输出 `SSIM` 和 `Error Rate` 浮点数值，同时输出一幅包含红黄蓝（或 Jet colormap）的直观偏差热力图。
- **[US-03] 结构化异常抛出能力（Machine-Readable）**
  当指标不达标（如 Error Rate > 5%），工具脚本能够将偏差最大点（X,Y坐标及差异项）以明确的文本指令/JSON 形式输出，确保 Agent 可以读取并生成对应的微调代码（Self-Healing Loop）。

## 6. 非功能口径
- 运算性能：整页热力图与指标测算（1440x810）要求在 2 秒内完成，不堵塞逐块渲染流程。

## 9. 变更记录

| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **v0.1** | 初始起草 | AI Coding Agent 基于人机讨论起草自愈工具链规范草案 | 待用户评审 |
