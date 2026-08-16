# Prompt 3: 起草执行任务清单 (tasks.md)

```markdown
plan.md 与 eval.md 已经过人工评审确认。请阅读确认版的 plan.md：
1. 任务拆解：参照 specs/templates/tasks.template.md 的结构起草 tasks.md；
2. 逐块任务链规划：针对各个视觉区块分别设立独立的 Task（如 T-02: Block 1 开发与切片验证、T-03: Block 2 开发与切片验证等）；
3. 交互式确认节点：在每个 Block 任务中明确包含「双图渲染（局部切片比对 + 累计全页预览）与用户确认节点」；
4. 硬性要求：每一个 Task 必须有明确可执行的 verify 命令（如 build --cumulative-up-to 与 render_and_diff 双图输出命令），严禁写“手工看一下”等不可自证的描述。
```
