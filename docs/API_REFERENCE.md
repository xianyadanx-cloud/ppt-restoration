# PPT Restoration API Reference

本文档提供了 PPT 智能还原工作空间（PPT Restoration Workspace）的核心引擎 `SlideBuilder`、弹性布局算子、Design Tokens 与相关工具链的完整 API 参考。

---

## 📐 1. 核心坐标系与设计约定

所有组件的空间定位统一基于 **0-1000 归一化坐标系**：
* 格式：`box = [left, top, width, height]`
* 范围：`left: 0`（左边缘）到 `left: 1000`（右边缘）；`top: 0`（顶部）到 `top: 1000`（底部）。
* 引擎自动将 `0-1000` 映射到 PPT 的实际页面物理尺寸（16:9 或 4:3 比例）。

---

## 🎨 2. Standard Design Tokens (`Tokens`)

位于 `from tools.pptx_helper import Tokens`。

| Token 常量 | 推荐值 (pt / scale) | 用途与场景 |
| :--- | :--- | :--- |
| `Tokens.FONT_HERO` | `36.0 pt` | 封面超大主标题 |
| `Tokens.FONT_TITLE_LG` | `32.0 pt` | 内页主标题 |
| `Tokens.FONT_TITLE_MD` | `24.0 pt` | 中号标题 |
| `Tokens.FONT_KPI_VAL` | `22.0 pt` | 核心 KPI 大字数字指标 (如 38万, 84%) |
| `Tokens.FONT_SECTION_H2` | `16.0 pt` | 卡片/分块大标题 |
| `Tokens.FONT_CARD_TITLE` | `14.0 pt` | 卡片内小节标题 |
| `Tokens.FONT_BODY` | `11.0 pt` | 标准正文 |
| `Tokens.FONT_BODY_SM` | `10.0 pt` | 次级说明文案/表格文字 |
| `Tokens.FONT_BADGE` | `8.5 pt` | 胶囊药丸/状态标签文字 |
| `Tokens.FONT_CAPTION` | `7.5 pt` | 脚注/说明微小字 |
| `Tokens.GAP_SM` | `8.0` (0-1000) | 卡片内部组件标准间距 |
| `Tokens.GAP_MD` | `14.0` (0-1000) | 卡片与卡片之间标准间距 |
| `Tokens.GAP_LG` | `20.0` (0-1000) | 跨板块大间距 |

---

## 🚀 3. 物理字符度量与防溢出拟合器

```python
from tools.pptx_helper import estimate_text_width_pt, calculate_safe_font_size

# 1. 物理测算中英文混合文本的真实渲染宽度 (磅值)
width_pt = estimate_text_width_pt("规模缺口 38万", font_size_pt=14)

# 2. 自动拟合安全字号 (超出容器单行宽度时自动降级字号，绝对不意外折行)
safe_size = calculate_safe_font_size(
    text="非常长的业务标题内容",
    target_width_pt=120.0,
    desired_font_size=16.0,
    min_font_size=8.0
)
```

---

## 🧩 4. 弹性流式与网格布局算子 (Flex & Grid)

### 4.1 弹性网格划分器 (`add_grid`)
```python
# 将大包围盒均匀切分成 3 列 1 行的子网格坐标 (自动处理间距)
cells = builder.add_grid(box=[50, 200, 900, 300], cols=3, rows=1, gap_x=16.0)
# cells = [(50, 200, 289.3, 300), (355.3, 200, 289.3, 300), (660.6, 200, 289.3, 300)]
```

### 4.2 弹性流式堆叠容器 (`add_stack`)
```python
# 自动垂直/水平排列子元素，居中对齐且等间距，无需 Agent 手动计算坐标！
builder.add_stack(
    box=[515, 192, 125, 105],
    direction="vertical",      # "vertical" 或 "horizontal"
    gap=Tokens.GAP_SM,         # 等间距
    align="center",            # 自动水平居中
    children=[
        {"type": "badge", "text": "规模缺口", "bg_color": "#FFFFFF", "text_color": "#0284C7"},
        {"type": "text", "text": "38万", "font_size": Tokens.FONT_KPI_VAL, "bold": True, "auto_fit_font": True},
        {"type": "badge", "text": "缺口16%", "bg_color": "#3B82F6", "text_color": "#FFFFFF"},
    ],
    bg_color="#F4F9FF",
    border_color="#BAE6FD"
)
```

### 4.3 复合语义行动卡片 (`add_flex_card`)
```python
builder.add_flex_card(
    box=[485, 325, 230, 280],
    badge="行动方案 A",
    kpi_value="84%",
    kpi_label="预期达成率",
    title="全渠道获客攻坚",
    subtitle="重点拓展华东与华南区域市场",
    body_items=["完成新渠道铺设", "留存率提升 5.2%"],
    bg_color="#FFFFFF",
    border_color="#CBD5E1",
    radius=True
)
```

---

## 🎨 5. `SlideBuilder` 原生构建方法清单

### 5.1 页面容器与卡片 (`add_card`)
```python
builder.add_card(
    box=[left, top, width, height], # 0-1000 归一化坐标
    bg_color="#F8FAFC",             # 背景颜色
    border_color="#E2E8F0",         # 边框颜色
    border_width_pt=1.0,            # 边框粗细 (pt)
    radius=True,                    # 是否圆角
    gradient_colors=["#1E5AA0", "#2B78C9"], # 渐变填充起止色
    gradient_angle=135.0            # 渐变角度
)
```

### 5.2 文本框与多段落排版 (`add_textbox`)
```python
builder.add_textbox(
    box=[left, top, width, height],
    text="标题或正文内容",
    font_size=Tokens.FONT_CARD_TITLE,
    font_color="#0F172A",
    bold=False,
    align="left",                   # "left", "center", "right"
    word_wrap=True,
    auto_fit_font=True              # 开启自动字符度量防溢出
)
```

### 5.3 原生表格与斑马纹 (`add_table`)
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
    font_size=10.5
)
```

### 5.4 珍珠发光进度条 (`add_progress_bar`)
```python
builder.add_progress_bar(
    box=[left, top, width, height],
    pct=0.84,                       # 进度百分比 (0.0 ~ 1.0)
    text="84%",                     # 进度文案
    bar_color="#C2410C",            # 进度条主色
    gradient_colors=["#8B2515", "#C2410C"], # 进度条渐变
    bg_color="#FCE4D6",             # 槽底背景色
    node_glow=True                  # 右侧高光珍珠节点
)
```

### 5.5 自由多边形与 3D 几何拼装 (`add_polygon`)
```python
builder.add_polygon(
    points=[(x1, y1), (x2, y2), (x3, y3), (x4, y4)], # 0-1000 顶点坐标序列
    fill_color="#1E3A8A",
    border_color="#3B82F6",
    gradient_colors=["#1E3A8A", "#3B82F6"],
    gradient_angle=45.0
)
```

### 5.6 保存演示文稿 (`save`)
```python
builder.save("output/slide_01.pptx")
```

---

## 🛠️ 6. 命令行辅助工具集 (CLI Tools)

| 工具脚本 | 命令示例 | 功能与输出 |
| :--- | :--- | :--- |
| **`tools/segment.py`** | `python tools/segment.py input/demo.png --scaffold` | 自动执行版式分析，输出分块图 `block_map.png` 与初始代码骨架 |
| **`tools/color_profiler.py`** | `python tools/color_profiler.py input/demo.png --box 35 100 930 80` | 量化指定选区的 Top-5 主色、渐变方向与边框色 |
| **`tools/render_and_diff.py`** | `python tools/render_and_diff.py output/step.pptx input/demo.png -o output/diff.png --crop-box 35 325 435 600` | 生成局部切片对比图与阶段性累计全页预览图 |
| **`tools/inspect_pptx.py`** | `python tools/inspect_pptx.py output/demo.pptx` | 检查 PPTX 的 DOM 树结构，严格验证 `PICTURE` 计数为 0 |
| **`tools/slice.py`** | `python tools/slice.py input/demo.png --box 100 100 200 200 -o assets/crop.png` | 依据 0-1000 归一化坐标裁剪高精度素材图片 |
| **`tools/merge.py`** | `python tools/merge.py output/slide_01.pptx output/slide_02.pptx -o output/final.pptx` | 将多个单页 PPTX 合并为完整 Deck |
