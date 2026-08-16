# Skill: Layout Auditor (几何与 DOM 质量断言)

> **Path**: `skills/layout-auditor/`
> **Role**: 对生成的 PPTX 进行全量 OpenXML DOM 扫描与设计几何规则静态断言，严格拦截错位、贴边与图片降维。

---

## 🎯 核心职责

1. **5 大几何与规范断言**：
   - Rule 1: `PICTURE == 0` (100% 纯原生矢量)；
   - Rule 2: `max_bottom <= 930` (底部呼吸空间)；
   - Rule 3: `top_delta <= 2.0` 且 `bottom_delta <= 3.0` (双栏对齐)；
   - Rule 4: 字阶合规断言；
   - Rule 5: 行内垂直居中。
2. **输出契约**：标准退出码 (0=PASS, 1=FAIL) 与格式化终端报告。
