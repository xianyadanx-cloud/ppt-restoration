---
specId: PLAN-FEAT-PPT-003-001
type: plan
parent_spec: spec.md
title: FEAT-PPT-003 技术架构与工程实施方案
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 待评审
confirmed: false
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, tasks.md, eval.md]
---

# PLAN-FEAT-PPT-003-001 ｜ 技术架构与工程实施方案

## 1. 架构总览 (Architecture Overview)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI Coding Agent (LLM 大脑)                       │
│  - 识别视觉隐喻 (3D透视书本 / 拟物板夹 / 咨询看板)                      │
│  - 制定 0-1000 空间蓝图与几何拓扑结构                                  │
│  - 编写基于 python-pptx 的 100% 纯原生矢量渲染代码                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ 调用与驱动
┌────────────────────────────────────▼────────────────────────────────────┐
│              Python 确定性视觉量化探针与渲染引擎 (底层工具集)           │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Canvas Calibrator: 自动识别并切除外围系统留白，归一化 16:9 画布     │
│ 2. Colorimeter Probe: 像素级 RGB 采样与 135°/90° 线性渐变色谱提取      │
│ 3. Typography Calibrator: pt = height_px * 0.667 精准字阶换算器        │
│ 4. Vector Geometry Builder: SlideBuilder 扩展 (add_polygon / rotation) │
│ 5. Visual Loopback Diff: 矢量图元仿真渲染与 Ground Truth 像素级比对    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 模块详细设计

### 模块 A: `tools/extract_visual_features.py` (视觉量化探针)
- **输入**：原始用户图片或截屏。
- **职责**：
  1. 扫描边缘像素，定位并裁剪真实幻灯片视口 `(min_x, min_y, max_x, max_y)`；
  2. 多点采样主色调、渐变受光面/阴影面、高亮指标色；
  3. 测量各层级文字的像素包围盒高度，输出推荐的 PowerPoint `Pt` 字阶值。

### 模块 B: `tools/pptx_helper.py` (扩展纯矢量渲染能力)
- **新增/强化能力**：
  - `add_polygon(points, bg_color, border_color, gradient_colors, rotation)`：支持 0-1000 点集自由多边形，线性渐变填充与任意角度旋转。
  - `add_textbox(..., rotation=float)`：原生支持文本框角度旋转（$\pm 7.0^\circ$），实现 3D 贴合。
  - `add_card(..., rotation=float)`：支持容器旋转。

### 模块 C: `tools/render_and_diff.py` (视觉闭环比对器)
- **职责**：解析 PPTX 的 DrawingML 矢量结构（Freeform/AutoShape/TextBox/GradFill），在 1440x810 画布上高保真模拟并生成左右对比图 `output/iteration_diff.png`。

## 8. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
