# Skill: Vector Builder (纯矢量代码生成)

> **Path**: `skills/vector-builder/`
> **Role**: 接收 `manifest.json` 结构化布局契约，通过确定性规则将其 1:1 编译为 `SlideBuilder` 原生 Python 函数，严格执行 `PICTURE=0`。

---

## 🎯 核心职责

1. **形状到 API 的精准映射**：
   - `SHAPE_CIRCLE` $\rightarrow$ `builder.add_badge(box=..., radius=True)`
   - `SHAPE_PILL` $\rightarrow$ `builder.add_badge(box=..., radius=True)`
   - `SHAPE_RECT_ROUNDED` $\rightarrow$ `builder.add_card(box=..., radius=True)`
   - `TEXT_PLAIN` $\rightarrow$ `builder.add_textbox(box=..., auto_fit_font=True)`
2. **防折行与 Design Tokens 自动注入**：
   - 自动绑定 `Tokens` 字阶与间距常数；
   - 开启 `auto_fit_font=True`。
