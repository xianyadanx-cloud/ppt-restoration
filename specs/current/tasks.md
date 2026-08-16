---
specId: TASKS-AUTO-HEAL-001
type: tasks
parent_spec: spec.md
plan_ref: plan.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 执行中
confirmed: true
version: 0.1
updated_at: 2026-08-16
execution_mode: sequential
related_specs: [eval.md]
---

# TASKS-AUTO-HEAL-001 ｜ 自动化视觉校验与自愈工具链 执行清单

## 执行期约束
- 不得违背 `plan.md §6 不改清单`（无 OpenCV 等第三方依赖）。
- 每个 Task 必须有明确可执行的 verify 命令。
- 采用交互式逐层开发，每完成一个模块需请求用户确认。

---

## 任务清单

### T-01 结构化属性对比引擎开发 (Layer 2)
- **任务内容**：增强 `tools/compare_properties.py`，支持读取目标区域（Bounding Box），提取 PPTX 原生组件参数，与预设 Ground Truth 构建差异矩阵。
- **产出物**：`tools/compare_properties.py`
- **verify 命令**：
  ```bash
  python tools/compare_properties.py output/slide_02.pptx input/slide_02.png
  ```
- **交互节点**：输出首个参数对比矩阵结果给用户确认。
- **状态**：[ ] 待执行

### T-02 图像量化偏差层开发 (Layer 1)
- **任务内容**：增强 `tools/diff_analyzer.py`，纯基于 `Pillow` 实现 SSIM 估算、Error Pixel Rate 计算，并生成彩色误差热力图（Thermal Heatmap）。
- **产出物**：`tools/diff_analyzer.py`
- **verify 命令**：
  ```bash
  python tools/diff_analyzer.py input/slide_02.png output/slide_02.png --heatmap
  ```
- **交互节点**：渲染并展示热力图与双指标 (SSIM/Error Rate) 供用户确认。
- **状态**：[ ] 待执行

### T-03 Agent 自愈指令适配层 (Layer 3)
- **任务内容**：将 T-01 与 T-02 的异常抛出封装为 JSON 或机器指令格式，抛出坐标 X,Y 与修复建议。
- **产出物**：`tools/diff_analyzer.py` / `tools/compare_properties.py`
- **verify 命令**：
  ```bash
  python tools/diff_analyzer.py input/slide_02.png output/slide_02.png --json
  ```
- **状态**：[ ] 待执行

### T-04 评测用例回填与判定签署
- **任务内容**：自动化回填 `eval.md` 并在通过后签署。
- **产出物**：`eval.md`
- **状态**：[ ] 待执行

### T-05 复盘沉淀与经验提炼
- **任务内容**：自动读取四份文档生成 `learnings.md`。
- **产出物**：`learnings.md`
- **状态**：[ ] 待执行
