---
specId: "SPEC-FEAT-PPT-004-001"
title: "复盘与经验沉淀 (Learnings): 消除多模态幻觉与非多模态架构设计模式"
status: "已固化"
version: "1.0"
---

# 1. 核心反模式与避坑指南 (Anti-Patterns)

### 🔴 严禁“脑补式嵌套大卡 (Over-Nested Cards)”
- **表现**：看到正文列表前有标题色块，就误以为整个正文都被包含在一个大底色卡片中。
- **根因**：多模态视觉模型的“语义先验”，缺乏像素级行背景检测。
- **防御法则**：任何时候在向 PPT 添加卡片前，必须先调用 `color_profiler.py` 扫描 Y 轴背景变化，只有当正文背景同样有持续底色时才允许使用 `full_card`；若仅标题行有底色，必须使用 `title_strip`。

---

# 2. 沉淀的标准设计模式 (Standard Design Patterns)

### 🟢 模式 1：条形标题底板 + 纯白裸排正文 (Title Strip + Plain Bullets)
```python
# 1. 仅为标题行添加条形微圆角底板 (高度 ~38)
builder.add_card(box=[488, 412, 474, 38], bg_color="#EDF6FD", border_color="transparent", radius=True)
builder.add_badge(box=[494, 416, 30, 30], text="1", bg_color="#1456AA", font_size=13, bold=True)
builder.add_textbox(box=[532, 416, 425, 30], text="流量重构-突破渠道瓶颈", font_size=15, font_color="#0F172A", bold=True)

# 2. 正文子弹项直接坐落于外层大白卡表面 (无嵌套底卡，设置 word_wrap=False 避免多余折行)
builder.add_textbox(box=[500, 456, 600, 22], text="• 阶梯式缩量: 对低效渠道实施每周10%的预算递减机制", font_size=10.5, font_color="#334155", word_wrap=False)
```

---

# 3. 工具链最佳实践 (Toolchain Best Practices)
1. **自动化取色**：优先使用 `python tools/color_profiler.py <img_path> --box L T W H`，直接获取数学确定的 HEX 色值与渐变。
2. **代码合成**：将页面元素维护在 `block_spec.json` 中，通过 `python tools/synth_code.py` 自动编译成 Python 代码。
3. **闭环修复**：通过 `python tools/error_localizer.py` 直接查看结构化机器修复建议。
