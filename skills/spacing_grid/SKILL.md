# Skill: Spacing & Grid Calculator (栅格与间距度量)

> **Path**: `skills/spacing-grid/`
> **Role**: 在 0-1000 归一化空间中，计算卡片容器内的栅格分割（Grid Matrix）、水平/垂直流式间距（Stack Gaps）、以及左右对称基准线。

---

## 🎯 核心职责

1. **栅格分发计算**：
   - 给定父容器 `box=[L, T, W, H]`、列数 `cols`、行数 `rows` 与间距 `gap_x`/`gap_y`，精确生成子单元格坐标。
2. **双栏基准线锁齐计算**：
   - 自动推导左右两栏主容器的最佳 `top`、`height` 与对称外边距。
3. **输出契约**：输出结构化 `layout_manifest.json`。
