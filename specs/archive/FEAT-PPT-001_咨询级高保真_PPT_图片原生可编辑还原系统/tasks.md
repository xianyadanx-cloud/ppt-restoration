---
specId: TASKS-PPT-001
type: tasks
parent_spec: spec.md
plan_ref: plan.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent & Human Reviewer
status: 已确认
confirmed: true
version: 1.0
updated_at: 2026-08-16
execution_mode: sequential
related_specs: [eval.md]
---

# TASKS-PPT-001 ｜ 执行任务清单与验证指令

## 执行期约束
- 严格遵循 `plan.md §6 不改清单`。
- 每完成一个 Task，必须运行对应的 **verify 命令** 且验证通过后，方可将状态标记为 `[x]` 并推进至下一个 Task。

---

## 任务清单

### T-01 核心排版引擎增强 (`tools/pptx_helper.py`)
- **任务内容**：实现 `add_progress_bar`（胶囊进度条+发光节点+数值）与 `add_kpi_card`（复合 KPI 指标卡+流向箭头）组件。
- **输出物**：[`tools/pptx_helper.py`](file:///Users/feng.liu/workspace/tools/pptx_helper.py)
- **verify 命令**：
  ```bash
  .venv/bin/python -m unittest tests/test_workspace.py
  ```
- **状态**：[x] 已完成（6 项单元测试 0.039s 全部通过）

---

### T-02 Slide 1 高保真重构与 3D 活页夹拟态分层 (`slides/build_slide_01.py`)
- **任务内容**：裁切 3D 活页夹无字底图，在 `slides/build_slide_01.py` 中分层叠加 6 组完全原生可编辑卡片、切角标签与中心“破局”书法图。
- **输出物**：[`slides/build_slide_01.py`](file:///Users/feng.liu/workspace/slides/build_slide_01.py) 与 [`output/slide_01.pptx`](file:///Users/feng.liu/workspace/output/slide_01.pptx)
- **verify 命令**：
  ```bash
  .venv/bin/python slides/build_slide_01.py && .venv/bin/python tools/inspect_pptx.py output/slide_01.pptx
  ```
- **状态**：[x] 已完成（生成 24 个原生 DOM 节点）

---

### T-03 Slide 2 高保真重构与原生进度条表格 (`slides/build_slide_02.py`)
- **任务内容**：重写 `slides/build_slide_02.py`，实现中段复合 KPI 指标卡、左下角带 5 组原生发光胶囊进度条的表格矩阵、右下角 135° 渐变《2+1破局行动》卡片。
- **输出物**：[`slides/build_slide_02.py`](file:///Users/feng.liu/workspace/slides/build_slide_02.py) 与 [`output/slide_02.pptx`](file:///Users/feng.liu/workspace/output/slide_02.pptx)
- **verify 命令**：
  ```bash
  .venv/bin/python slides/build_slide_02.py && .venv/bin/python tools/inspect_pptx.py output/slide_02.pptx
  ```
- **状态**：[x] 已完成（生成 64 个原生 DOM 节点）

---

### T-04 终版两页演示文稿合并 (`output/presentation_IMG_7410.pptx`)
- **任务内容**：运行 `merge.py` 将两页高质量幻灯片合并为单一演示文稿，并完成 DOM 结构校验。
- **输出物**：[`output/presentation_IMG_7410.pptx`](file:///Users/feng.liu/workspace/output/presentation_IMG_7410.pptx)
- **verify 命令**：
  ```bash
  .venv/bin/python tools/merge.py output/slide_01.pptx output/slide_02.pptx -o output/presentation_IMG_7410.pptx && .venv/bin/python tools/inspect_pptx.py output/presentation_IMG_7410.pptx
  ```
- **状态**：[x] 已完成（合并 2 页共 88 个原生 DOM 节点）

---

### T-05 评测验收与结果回填 (`eval.md`)
- **任务内容**：核对 `spec.md` 中定义的 US-01 ~ US-05 验收标准，完成测试并回填判定结论。
- **输出物**：[`eval.md`](file:///Users/feng.liu/workspace/eval.md)
- **verify 命令**：
  ```bash
  .venv/bin/python -m unittest tests/test_workspace.py
  ```
- **状态**：[x] 已完成（AC 覆盖率 100%，判定结论【通过】）

---

### T-06 复盘沉淀与经验提炼 (`learnings.md`)
- **任务内容**：自动提炼从“扁平死盒子”到“3D分层+原生进度条”重构全过程的教训与经验。
- **输出物**：[`learnings.md`](file:///Users/feng.liu/workspace/learnings.md)
- **状态**：[x] 已完成（沉淀 L-01~L-04 核心工程实践卡片）
