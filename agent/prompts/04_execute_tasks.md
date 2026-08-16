# Prompt 4: 执行任务与自测回填

```markdown
spec.md、plan.md、tasks.md、eval.md 均已确认。
1. 严格按照 tasks.md 规划的任务链（逐个 Block）顺序执行实现；
2. 逐块交付与呈报：每完成一个 Block，必须立即运行 verify 命令生成「局部切片比对图 (Slice Diff)」+「累计全页预览图 (Cumulative Preview)」并呈报给用户确认；
3. 原地阻塞自愈：若用户提出微调意见，原地在当前 Block 修复并重新验证，直到用户确认无误后方可推进下一 Block；通过后将当前 Task 标记为 [x]；
4. 严格遵守 plan.md §6 "不改清单" 的硬约束（100% 原生矢量渲染，PICTURE=0）；
5. 全部 Block 通过用户确认后，运行全页回归测试与 DOM 检查，将最终测试结果回填至 eval.md。
```
