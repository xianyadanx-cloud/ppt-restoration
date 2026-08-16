---
specId: SPEC-<PROJECT>-001
type: spec
title: <项目/幻灯片还原规格名称>
domain: 演示文稿/文档生成
system: ppt-restoration-workspace
owner: <负责人 / AI Coding Agent>
status: 草稿          # 草稿 / 待评审 / 已确认
confirmed: false       # 人评审纠错补充后改为 true
version: 0.1
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
tier: medium           # light / medium / heavy
related_specs: [plan.md, eval.md, tasks.md]
---

# SPEC-<PROJECT>-001 ｜ <项目名称> 需求规格说明书

## 1. 背景与目标
阐述为什么做本次还原/开发、目标交付物是什么。用清晰准确的语言说明输入素材与预期交付标准。

## 2. 业务语义与元语消歧（AI 必读，先于一切）
消除所有潜在歧义：
- 哪些属于 3D 拟态底图容器？哪些属于必须 100% 原生可编辑的图层？
- 复杂图表（进度条、KPI 指标卡、数据表格）的具体呈现形式与交互要求。

### 2.1 裁决与盲区确认表

| 序号 | 待裁决项 / 潜在盲区 | 暂定结论与处理口径 | 裁决依据 |
| :--- | :--- | :--- | :--- |
| **D-01** | <盲区1描述> | <Agent暂定结论> | <判定理由> |
| **D-02** | <盲区2描述> | <Agent暂定结论> | <判定理由> |

## 3. 范围与场景（Scope）
- **In Scope**：明确本次迭代必须覆盖的页面、组件与特性。
- **Out of Scope**：明确本次迭代不涉及的内容（如复杂宏脚本、音视频嵌入）。

## 5. 验收标准（Acceptance Criteria）
以 `US-编号` 细化每条验收指标，供 `eval.md` 逐条矩阵核验：
- **[US-01]** <指标1：如 3D 视觉隐喻与空间透视保真度>
- **[US-02]** <指标2：如 数据图表/进度条组件原生渲染>
- **[US-03]** <指标3：如 100% 文本原生可编辑与字阶规范>

## 6. 非功能口径
- 性能/耗时门槛、依赖约束（如零云端 API 依赖）。

## 9. 变更记录

| 版本 | 变更类型 | 变更内容说明 | 评审人 |
| :--- | :--- | :--- | :--- |
| **v0.1** | 初始起草 | Agent 依据原始素材起草需求规格草案 | Coding Agent |
