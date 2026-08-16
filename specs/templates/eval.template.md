---
specId: EVAL-<PROJECT>-001
type: eval
parent_spec: spec.md
plan_ref: plan.md
tasks_ref: tasks.md
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: <负责人 / AI Coding Agent>
status: 草稿
confirmed: false
version: 0.1
updated_at: <YYYY-MM-DD>
related_specs: [spec.md, plan.md, tasks.md]
---

# EVAL-<PROJECT>-001 ｜ 验收评测矩阵与测试用例

## 0. 评测概况
- **测试目标**：验证还原产物在视觉隐喻、数据可视化、排版字阶与 100% 原生可编辑性的达成情况。
- **执行方式**：自动化单元测试 + DOM 树形态分析 + 原图对比核验。

---

## 1. AC 覆盖与验收矩阵

| 需求编号 | 验收标准说明 | 验证方法与检查点 | 状态 | 判定详情 |
| :--- | :--- | :--- | :--- | :--- |
| **US-01** | <指标1说明> | <具体检查点> | [ ] 待测 | <回填结果> |
| **US-02** | <指标2说明> | <具体检查点> | [ ] 待测 | <回填结果> |
| **US-03** | <指标3说明> | <具体检查点> | [ ] 待测 | <回填结果> |

---

## 3. 降级与容错验证
- [ ] 底图切片缺失时，平滑降级为纯矢量几何卡片。
- [ ] OfficeCLI 缺失时，自动降级为 DOM Inspector 自检报告。

---

## 5. 不改清单核对
- [ ] 严禁文字贴图：所有文字为原生 TextFrame。
- [ ] 严格 0-1000 坐标规范。

---

## 7. 判定结论
- **综合评定**：待回填（通过 / 有条件通过 / 不通过）
- **判定理由**：
- **判定人（verdict_by）**：
