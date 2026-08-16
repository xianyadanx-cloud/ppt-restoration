---
specId: TASKS-<PROJECT>-001
type: tasks
parent_spec: spec.md
plan_ref: plan.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: <负责人 / AI Coding Agent>
status: 草稿
confirmed: false
version: 0.1
updated_at: <YYYY-MM-DD>
execution_mode: sequential
related_specs: [eval.md]
---

# TASKS-<PROJECT>-001 ｜ 执行任务清单与验证指令

## 执行期约束
- 不得违背 `plan.md §6 不改清单`。
- 每完成一个 Task，必须执行其绑定的 **verify 命令** 且验证通过后，方可在"状态"列打勾 `[x]` 并进入下一个任务。

---

## 任务清单

### T-01 核心工具库或排版微组件增强
- **任务内容**：实现所需的排版微组件（如进度条、KPI 指标卡）。
- **产出物**：`tools/pptx_helper.py`
- **verify 命令**：
  ```bash
  .venv/bin/python -m unittest tests/test_workspace.py
  ```
- **状态**：[ ] 待执行

### T-02 单页幻灯片构建与高保真分层实现
- **任务内容**：编写 `slides/build_slide_XX.py` 还原幻灯片内容。
- **产出物**：`slides/build_slide_XX.py` 与 `output/slide_XX.pptx`
- **verify 命令**：
  ```bash
  .venv/bin/python slides/build_slide_XX.py && .venv/bin/python tools/inspect_pptx.py output/slide_XX.pptx
  ```
- **状态**：[ ] 待执行

### T-03 多页合并与 DOM 结构检查
- **任务内容**：合并并校验完整演示文稿。
- **产出物**：`output/presentation_<NAME>.pptx`
- **verify 命令**：
  ```bash
  .venv/bin/python tools/merge.py ... -o output/presentation_<NAME>.pptx && .venv/bin/python tools/inspect_pptx.py output/presentation_<NAME>.pptx
  ```
- **状态**：[ ] 待执行

### T-04 评测用例回填与判定签署
- **任务内容**：回填 `eval.md` 并在通过后签署。
- **产出物**：`eval.md`
- **状态**：[ ] 待执行

### T-05 复盘沉淀与经验提炼
- **任务内容**：自动读取四份文档生成 `learnings.md`。
- **产出物**：`learnings.md`
- **状态**：[ ] 待执行
