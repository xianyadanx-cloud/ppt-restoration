---
specId: "SPEC-FEAT-PPT-004-001"
title: "任务分解与执行清单 (Tasks): 非多模态自动化工具链"
status: "已完成"
version: "1.0"
---

# 任务清单 (Task Checklist)

- [x] **Task 1: 实现全自动色彩与渐变提取器**
  - [x] 1.1 编写 `tools/color_profiler.py`，支持 K-Means 聚类与 0-1000 归一化输入
  - [x] 1.2 编写渐变方向与水平/垂直色阶采样算法
  - [x] 1.3 编写边框颜色与粗细探测算法

- [x] **Task 2: 实现 Y 轴背景色阶突变与子容器探测**
  - [x] 2.1 在 `color_profiler.py` 中编写 `detect_vertical_strips` 算法
  - [x] 2.2 自动分类 `title_strip` (局部标题底条)、`full_card` (整体底卡) 与 `plain_text_area` (纯白正文)
  - [x] 2.3 实测 Block 5 行动区域并成功提取两个独立 `title_strip` 与纯白正文

- [x] **Task 3: 实现结构化像素误差定位器**
  - [x] 3.1 编写 `tools/error_localizer.py`，支持读取 spec JSON 并逐元素比对 $\Delta E$
  - [x] 3.2 自动输出可执行的修复代码建议（如 `bg_color="..."`）

- [x] **Task 4: 实现声明式 JSON 到 Python 代码合成器**
  - [x] 4.1 编写 `tools/synth_code.py`，映射卡片、文本、徽章、表格与进度条
  - [x] 4.2 自动合成模块化函数与 CLI 接口

- [x] **Task 5: 真实场景端到端闭环验证 (Block 5 纠正实测)**
  - [x] 5.1 纠正 Block 5 结构：去除巨大蓝底卡，仅在标题行保留淡蓝条形底板，正文直接坐落纯白底板
  - [x] 5.2 重新编译 `output/slide_02.pptx` 并生成 `output/diff_block5_true_verified.png`
  - [x] 5.3 经用户与视觉对账确认效果完美一致

- [x] **Task 6: 固化知识库与 SOP 规范**
  - [x] 6.1 将非多模态工具链流程完整写入 `agent/AGENTS.md`
  - [x] 6.2 完善 `specs/eval.md` 与 `specs/learnings.md` 并完成 SDD 验收

## 变更记录
| 日期 | 变更说明 | 责任人 |
| :--- | :--- | :--- |
| **2026-08-16** | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 单元测试同步校验 | Agent/Human |
