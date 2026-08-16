# PPT Restoration API Reference

本文档提供了 PPT 智能还原工作空间（PPT Restoration Workspace）的核心引擎 `SlideBuilder` 及相关工具链的完整 API 参考。

---

## 📐 1. 核心坐标系与设计约定

所有组件的空间定位统一基于 **0-1000 归一化坐标系**：
* 格式：`box = [left, top, width, height]`
* 范围：`left: 0`（左边缘）到 `left: 1000`（右边缘）；`top: 0`（顶部）到 `top: 1000`（底部）。
* 引擎自动将 `0-1000` 映射到 PPT 的实际页面物理尺寸（16:9 或 4:3 比例）。

---

## 🎨 2. `SlideBuilder` 核心类 API

位于 [`tools/pptx_helper.py`](file:///Users/feng.liu/workspace/tools/pptx_helper.py)。

### 2.1 初始化
```python
from tools.pptx_helper import SlideBuilder

builder = SlideBuilder(
    aspect_ratio="16:9",       # "16:9" (默认) 或 "4:3"
    bg_color="#FFFFFF",         # 页面纯色背景 (HEX / RGBColor / 命名色)
    gradient_bg=None,          # 页面渐变背景 ["#1E3A8A", "#0F172A"]
    gradient_angle=90.0        # 渐变角度 (度数, 0~360)
)
```

### 2.2 页面容器与卡片 (`add_card`)
```python
builder.add_card(
    box=[left, top, width, height], # 0-1000 归一化坐标
    bg_color="#F8FAFC",             # 背景颜色
    border_color="#E2E8F0",         # 边框颜色
    border_width=1.0,               # 边框粗细 (pt)
    radius=True,                    # 是否圆角 (True 为圆角矩形, False 为直角)
    gradient_colors=["#1E5AA0", "#2B78C9"], # 渐变填充起止色 (可选)
    gradient_angle=135.0,           # 渐变角度
    opacity=1.0                     # 不透明度
)
```

### 2.3 文本框与多段落排版 (`add_textbox`)
```python
builder.add_textbox(
    box=[left, top, width, height],
    text="标题或正文内容",
    font_size=14,                   # 字号 (pt)
    font_color="#0F172A",           # 文字颜色
    bold=False,                     # 是否加粗
    align="left",                   # 对齐方式: "left", "center", "right"
    vertical_align="top",           # 垂直对齐: "top", "middle", "bottom"
    font_name="Microsoft YaHei",    # 字体名称 (默认微软雅黑/Arial)
    word_wrap=True                  # 是否自动换行
)
```

### 2.4 药丸与徽章标签 (`add_badge`)
```python
builder.add_badge(
    box=[left, top, width, height],
    text="核心指标",
    bg_color="#2563EB",             # 标签背景色
    text_color="#FFFFFF",           # 标签文字色
    border_color=None,              # 描边色
    font_size=9,                    # 字号
    bold=True                       # 加粗
)
```

### 2.5 复合 KPI 卡片 (`add_kpi_card`)
```python
builder.add_kpi_card(
    box=[left, top, width, height],
    top_tag="规模缺口",             # 顶部外凸徽章文案
    value="38万",                  # 核心大字指标
    subtext="较上季度增加12%",       # 说明小字
    bottom_badge="缺口16%",        # 底部胶囊标签
    bg_color="#F4F9FF",
    border_color="#BAE6FD"
)
```

### 2.6 原生表格与斑马纹 (`add_table`)
```python
builder.add_table(
    box=[left, top, width, height],
    headers=["项目名称", "目标值", "实际值", "整体完成率"],
    rows=[
        ["新用户招募", "45万", "38万", ""],
        ["用户留存率", "70%", "69%", ""],
    ],
    col_widths=[85, 55, 55, 200],   # 列宽权重占比
    header_bg="#1D64B2",            # 表头背景色
    header_color="#FFFFFF",         # 表头文字色
    row_bg_colors=["#FFFFFF", "#FEF3F2"], # 斑马纹行背景色交替列表
    font_size=10.5,
    align="left"
)
```

### 2.7 珍珠发光进度条 (`add_progress_bar`)
```python
builder.add_progress_bar(
    box=[left, top, width, height],
    pct=0.84,                       # 进度百分比 (0.0 ~ 1.0)
    text="84%",                     # 进度文案
    bar_color="#C2410C",            # 进度条主色
    gradient_colors=["#8B2515", "#C2410C"], # 进度条渐变填充 (可选)
    bg_color="#FCE4D6",             # 槽底背景色
    node_glow=True,                 # 右侧是否添加高光珍珠节点
    font_size=10,
    text_color="#9A3412"
)
```

### 2.8 自由多边形与 3D 几何拼装 (`add_polygon`)
```python
builder.add_polygon(
    points=[(x1, y1), (x2, y2), (x3, y3), (x4, y4)], # 0-1000 顶点坐标序列
    fill_color="#1E3A8A",
    border_color="#3B82F6",
    border_width=1.0,
    gradient_colors=["#1E3A8A", "#3B82F6"],
    gradient_angle=45.0
)
```

### 2.9 原生图表 (`add_chart`)
```python
builder.add_chart(
    box=[left, top, width, height],
    chart_type="column",            # "column", "bar", "line", "pie", "doughnut", "area"
    categories=["Q1", "Q2", "Q3", "Q4"],
    series=[
        {"name": "2025年", "values": [120, 150, 180, 220], "color": "#2563EB"},
        {"name": "2026年", "values": [140, 190, 240, 310], "color": "#10B981"}
    ],
    has_legend=True,
    legend_position="top"
)
```

### 2.10 保存演示文稿 (`save`)
```python
builder.save("output/slide_01.pptx")
```

---

## 🛠️ 3. 命令行辅助工具集 (CLI Tools)

| 工具脚本 | 命令示例 | 功能与输出 |
| :--- | :--- | :--- |
| **`tools/segment.py`** | `python tools/segment.py input/demo.png --scaffold` | 自动执行版式分析，输出分块图 `block_map.png` 与初始代码骨架 |
| **`tools/color_profiler.py`** | `python tools/color_profiler.py input/demo.png --box 35 100 930 80` | 量化指定选区的 Top-5 主色、渐变方向与边框色 |
| **`tools/render_and_diff.py`** | `python tools/render_and_diff.py output/step.pptx input/demo.png -o output/diff.png --crop-box 35 325 435 600` | 生成局部切片对比图与截至当前的累计全页预览图 |
| **`tools/inspect_pptx.py`** | `python tools/inspect_pptx.py output/demo.pptx` | 检查 PPTX 的 DOM 树结构，严格验证 `PICTURE` 计数为 0 |
| **`tools/slice.py`** | `python tools/slice.py input/demo.png --box 100 100 200 200 -o assets/crop.png` | 依据 0-1000 归一化坐标裁剪高精度素材图片 |
| **`tools/merge.py`** | `python tools/merge.py output/slide_01.pptx output/slide_02.pptx -o output/final.pptx` | 将多个单页 PPTX 合并为完整 Deck |
