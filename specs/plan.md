---
specId: "SPEC-FEAT-PPT-004-001"
title: "技术实现方案与架构设计 (Plan): 非多模态自动化工具链架构"
status: "已批准"
version: "1.0"
---

# 1. 架构总览 (Architecture Overview)

```
[ input/<name>.png ]
        │
        ├──▶ tools/segment_auto.py    (自动分块与投影直方图分析)
        │           │
        │           ▼
        ├──▶ tools/color_profiler.py  (K-Means 聚色 + Y轴色阶突变探测 + 渐变识别)
        │           │
        │           ▼
        │    [ specs/<name>_spec.json ] (声明式结构规格)
        │           │
        │           ▼
        ├──▶ tools/synth_code.py      (JSON-to-Code 矢量代码合成器)
        │           │
        │           ▼
        │    [ slides/build_<name>.py ]
        │           │
        │           ▼
        ├──▶ tools/render_and_diff.py (100% 矢量 PPTX 渲染 + PIL 对账)
        │           │
        │           ▼
        └──▶ tools/error_localizer.py (结构化误差定位 + 自动修复指令闭环)
```

---

# 2. 核心模块设计 (Component Design)

### 2.1 `tools/color_profiler.py` (色阶与子容器探测引擎)
- **输入**：`img_path`, `box_norm` [left, top, width, height]
- **算法流程**：
  1. 归一化坐标转换与内部安全采样（避开 3px 外框模糊）；
  2. K-Means 聚类提取 5 大主色；
  3. 水平/垂直色差投影比较判定渐变方向及起止 HEX 色；
  4. `detect_vertical_strips`：扫描中轴 60% 宽度，按连通域高度阈值（$15 \le h \le 55$）自动划分 `title_strip` 与 `plain_text_area`。

### 2.2 `tools/synth_code.py` (代码合成引擎)
- **输入**：`block_spec.json`
- **生成产物**：符合 `SlideBuilder` 标准调用语法的 Python 脚本。
- **特性**：
  - 自动解耦为独立的 `add_<block>_section(builder)` 函数；
  - 自动组装 `build_<name>()` 累加构建与 CLI 接口。

### 2.3 `tools/error_localizer.py` (像素误差定位引擎)
- **输入**：`pptx_path`, `orig_img_path`, `spec_json`
- **输出**：结构化 JSON 错误清单与修复指令。

---

# 3. 依赖与环境约束 (Dependencies & Constraints)
- **核心依赖**：`Pillow` (PIL), `python-pptx`, `lxml`（纯 Python + 数学计算，零外部第三方大模型 API 依赖）。
- **空间坐标**：全面遵循 `0-1000` 归一化规范。

## 8. 变更记录
| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
| **2026-08-16** | 变更调优 | 单元测试同步校验 | Agent/Human |
