# Skill: Element Profiler (微观元素几何与属性探测)

> **Path**: `skills/element-profiler/`
> **Role**: 输入局部切片图像，通过轮廓分析、圆度计算与 K-Means 色彩聚类，确定性输出元素的几何形状、色彩、字阶与内外边距。

---

## 🎯 核心职责

1. **确定性形状分类 (Contour Circularity)**：
   - 计算圆度指标 $\text{Circularity} = \frac{4\pi \cdot \text{Area}}{\text{Perimeter}^2}$：
     - 若 $\ge 0.85$ 且宽高比 $\approx 1.0 \rightarrow$ **`SHAPE_CIRCLE` (正圆)**
     - 若 $\ge 0.75$ 且宽高比 $> 1.5 \rightarrow$ **`SHAPE_PILL` (胶囊/药丸)**
     - 若角点为 4 且有圆角 $\rightarrow$ **`SHAPE_RECT_ROUNDED` (圆角矩形)**
     - 否则判定为 **`SHAPE_RECT_SHARP` (直角矩形)** 或 **`TEXT_PLAIN` (纯文本)**
2. **微观色彩提取**：
   - 提取 Top-3 主色 HEX，探测起止色与渐变方向。
3. **输出契约**：输出机器可读的 `element_manifest.json`。
