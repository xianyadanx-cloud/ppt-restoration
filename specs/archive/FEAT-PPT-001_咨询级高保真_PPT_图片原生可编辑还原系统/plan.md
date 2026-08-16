---
specId: PLAN-PPT-001
type: plan
parent_spec: spec.md
title: 咨询级高保真 PPT 原生还原架构设计与重构方案
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: AI Coding Agent & Human Reviewer
status: 已确认
confirmed: true
version: 1.0
created_at: 2026-08-16
updated_at: 2026-08-16
related_specs: [spec.md, eval.md, tasks.md]
---

# PLAN-PPT-001 ｜ 咨询级高保真 PPT 原生还原技术架构与方案设计

## 1. 系统分层架构（4-Layer Rendering Pipeline）

```mermaid
flowchart TD
    subgraph Layer4 [第 4 层: 原生富文本层 (100% 原生可编辑)]
        L4[所有标题、指标数据、正文段落、Bullet 列表]
    end

    subgraph Layer3 [第 3 层: 原生数据可视化与进度条层]
        L3[add_progress_bar 发光胶囊进度条 / 原生图表 / 原生表格]
    end

    subgraph Layer2 [第 2 层: 原生矢量几何卡片层]
        L2[add_card 圆角白底卡片 / add_kpi_card 复合指标卡 / add_badge]
    end

    subgraph Layer1 [第 1 层: 底图与 3D 拟态透视层]
        L1[3D 对开折页书本无字底图切片 / 幻灯片背景]
    end

    Layer1 --> Layer2 --> Layer3 --> Layer4
```

---

## 2. 核心组件扩展设计 (`tools/pptx_helper.py`)

### 2.1 胶囊进度条组件 (`add_progress_bar`)
用于解决 Slide 2 核心战役表格中“整体完成率”从图形退化为纯文本的问题：
```python
def add_progress_bar(
    box: List[float],
    pct: float,  # 0.0 ~ 1.0 (e.g. 0.84 for 84%)
    bar_color: str = "#C2410C",
    bg_color: str = "#FED7AA",
    show_text: bool = True,
    text: Optional[str] = "84%",
    node_glow: bool = True,
) -> None:
    # 1. 绘制底层淡色胶囊背景槽
    # 2. 根据 pct 绘制当前进度的主题色胶囊
    # 3. 在进度条终点端部绘制高亮白色发光小圆点 (node_glow)
    # 4. 右侧绘制原生百分比文字
```

### 2.2 复合 KPI 胶囊卡片 (`add_kpi_card`)
用于解决中段 3 个 KPI 指标卡比例失调问题：
- 顶部淡色小胶囊（`规模缺口`）
- 中间巨号粗体数字（`38万`）
- 底部悬浮深色胶囊（`缺口16%`）

### 2.3 3D 折页书本分层复原
- 裁切 `input/slide_01.png` 中间的 3D 对开活页夹底图到 `assets/slide1_book_bg.png`；
- 作为 Slide 1 的局部容器底图，上层严丝合缝叠加 6 组原生白底卡片与文本框。

---

## 5. 降级与容错设计

- **切片底图降级**：若未检测到特定 3D 切片底图，自动回退到原生矢量矩形容器，保证代码在任何情况下均能生成有效 `.pptx`。
- **渲染工具降级**：`tools/verify.py` 依次回退：`OfficeCLI -> Keynote -> LibreOffice -> DOM Inspector`。

---

## 6. 不改清单（硬约束，编码时绝对不能碰）

1. **绝对严禁将文字内容截图当图片贴入**：所有中英文字符、百分比、数字必须保持为原生可编辑的 `TextFrame`。
2. **坐标体系硬锁定**：所有空间传参必须严格限制在 `0-1000` 归一化坐标系内。
3. **保持 tools 公共 API 向后兼容**：不破坏已有的 `add_card`, `add_header`, `add_textbox`, `add_chart`, `add_table` 方法签名。

---

## 8. 变更记录

| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **v1.0** | 初始确认 | 遵循 zszc_ai_coding SDD 规范完成 plan.md 4 层分层架构与新增进度条/KPI组件设计 | Human Reviewer |
