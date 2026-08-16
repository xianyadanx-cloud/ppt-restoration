---
specId: "SPEC-FEAT-PPT-009"
title: "技术方案与架构设计说明书 (Plan): 纵向弹性均分算子与空洞质检断言"
version: "1.0"
status: "已批准"
last_updated: "2026-08-16"
authors: ["Antigravity", "feng.liu"]
---

# 技术方案与架构设计说明书 (Plan)

## 📐 1. 算法与断言架构

```mermaid
flowchart TD
    S2["skills/spacing_grid/grid_calculator.py<br/>distribute_vertical_sections"] --> Calc["计算: 净可用高 418px / 2模块<br/>-> 模块高 175px, 中缝 gap 40px"]
    Calc --> Slide["slides/build_slide_02.py<br/>行动 1 (405~580) + 行动 2 (620~795) + 底栏 (845~920)"]
    Slide --> Audit["skills/layout_auditor/auditor.py<br/>Rule 6: 检查相邻 gap <= 70px<br/>检查填充率 >= 70%"]
    Audit --> Pass["✅ ALL PASSED"]
```

---

## 📝 2. 详细改造内容

1. **`skills/spacing_grid/grid_calculator.py`**：
```python
def distribute_vertical_sections(
    container_top: float,
    container_height: float,
    count: int,
    header_h: float = 76.0,
    footer_h: float = 75.0,
    top_margin: float = 24.0,
    bottom_margin: float = 20.0,
    gap_y: float = 35.0,
) -> List[Dict[str, float]]:
    ...
```

2. **`tools/layout_linter.py` & `skills/layout_auditor/auditor.py`**：
```python
# Rule 6: No giant void gap in large containers
if any_gap > 75.0:
    errors.append(f"[RULE 6: GIANT_VOID_GAP] Detected empty gap of {any_gap:.1f}px between vertical modules (max allowed <= 70px).")
```

## 8. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
