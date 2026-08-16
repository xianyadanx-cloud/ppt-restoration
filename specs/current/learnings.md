---
specId: LEARNINGS-AUTO-HEAL-001
type: learnings
parent_spec: spec.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent
status: 归档
confirmed: true
version: 1.0
updated_at: 2026-08-16
related_specs: [spec.md, plan.md, tasks.md, eval.md]
---

# LEARNINGS-AUTO-HEAL-001 ｜ 实战经验复盘沉淀 (Auto-Healing Toolchain)

## 🎯 核心认知跃迁
在本次迭代中，我们实现了“从定性视觉比对到定量指标自愈”的底层工具链跃迁。
**最大洞察**：单纯依赖 VLM大模型（Vision-Language Model）做“看图找茬”无法完成最后 5% 的像素级对齐收敛。只有通过**底层 DOM 参数抽取对比（Layer 2）**与**确定性的像素差异热力及坐标（Layer 1）**相叠加，并抛出 JSON 格式的修正建议（Layer 3），才能真正实现 Agent 的无人值守自动微调闭环。

---

### 📌 [L-01] 零依赖图像量化框架的可行性
- **问题现象**：过去一提到计算机视觉差异计算，往往立刻引入 `OpenCV` 或 `skimage`，导致工具链极其沉重。
- **根本原因**：惯性思维。
- **修复方案与最佳实践**：我们完全通过纯 `Pillow (PIL)` 及其像素遍历和基础数学库（`math`），成功近似实现了高精度的局部 SSIM 计算以及 Jet 风格彩色热力图映射。这极大保持了 `tools` 的轻量化特征。
- **可复用性**：极高。任何受限的 Agent 运行沙箱环境均可无缝拉起该工具。

---

### 📌 [L-02] 机器可读接口 (Machine-Readable Output) 的至关重要
- **问题现象**：人类看着漂亮的 CLI 彩色表格和三联图能够快速定位错位，但如果是 Agent 的上层 State Machine，这种长文本难以稳定解析。
- **根本原因**：工具只面向人，未面向“机器调用”。
- **修复方案与最佳实践**：为所有工具提供独立的 `--json` CLI 参数，切断所有华丽的 ASCII Border 输出，单纯 dumps 原生的 `dict` 结构，提供如 `max_error_coord_px: {"x": 50, "y": 86}` 这样高度精确的数据。
- **可复用性**：极高。后续所有提供给 Agent 的诊断脚本，都应默认支持 `--json` 解析模式。
