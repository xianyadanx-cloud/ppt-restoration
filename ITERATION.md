# 鱼丸两页视觉还原迭代

金样例是「目标追溯 / 工作目标拆解」两页，规范画布 1440×810。对比一律用 LibreOffice 24.2 渲染后缩放到画布再算项目指标。左图为原图，右图为还原。本机没有 PowerPoint，正式 PASS 不可用，下列数字都是 PREVERIFIED。

用户给出的旧基线是残页：case1 SSIM ≈ 0.635（底部时间轴和后两行被切掉），case2 SSIM ≈ 0.590（接近 OCR 碎字墙）。本轮从完整页面重新做，所以 case1 的 SSIM 不能和那次残页直接比高低，文字墨迹重叠（ink IoU）和模糊 L1 更能说明有没有对齐。

## 指标

| 轮次 | case1 SSIM | case1 ink IoU | case1 blur L1 | case2 SSIM | case2 ink IoU | case2 blur L1 |
|---|---:|---:|---:|---:|---:|---:|
| 1 初版整页 | 0.453 | 0.385 | 0.066 | 0.525 | 0.362 | 0.079 |
| 2 季度卡片与栏目 | 0.477 | 0.319 | 0.065 | 0.582 | 0.375 | 0.071 |
| 3 按像素墨迹重排 | 0.622 | 0.632 | 0.037 | 0.637 | 0.495 | 0.049 |
| 4 拆开中西文、收箭头 | 0.628 | 0.626 | 0.038 | 0.637 | 0.497 | 0.050 |
| 5 字重与箭头尖 | 0.627 | 0.625 | 0.038 | 0.637 | 0.499 | 0.050 |

第 3 轮是结构对齐：case1 ink IoU 从 0.32 升到 0.63，blur L1 从 0.065 降到 0.037。case2 SSIM 从碎字墙基线 0.590 升到 0.637，版面不再是字符墙。第 4、5 轮人眼差异继续变小，像素 SSIM 已经贴在字体光栅的平台上，几乎不再动。

## 每轮改了什么

1. 去掉主题阴影和自动换行，用闭式字号把两页搭出来。几何是目测的，文字整体错位，差异图是重影。
2. 补上四季度卡片、时间轴和 case2 的三栏。`homePlate` 在 python-pptx 里没有枚举，箭头被静默丢掉。
3. 从原图像素量出标题、正文行、卡片、KPI、时间轴圆点的墨迹盒和色值，按 LibreOffice 实测的上升线偏移摆字。case2 插画和三个图标用原图裁剪，图标加圆形透明蒙版，避免方块把邻栏文字烤进去。
4. LibreOffice 会在汉字和 `/`、数字、`@` 之间插入大约 10px 的空隙，`spc` 对它无效。中西文拆成相邻文本框，空隙回到 3–6px。标题墨迹宽从 792px 收到 759px（原图 748px）。
5. 页眉账号改回加粗，季度箭头尖调浅，飘带文字避开图标。

对比图：

- [第 1 轮 case1](docs/iteration/round1_case1.png) / [case2](docs/iteration/round1_case2.png)
- [第 2 轮 case1](docs/iteration/round2_case1.png) / [case2](docs/iteration/round2_case2.png)
- [第 3 轮 case1](docs/iteration/round3_case1.png) / [case2](docs/iteration/round3_case2.png)
- [第 4 轮 case1](docs/iteration/round4_case1.png) / [case2](docs/iteration/round4_case2.png)
- [第 5 轮 case1](docs/iteration/round5_case1.png) / [case2](docs/iteration/round5_case2.png)

## 代码侧能力

这些改动进了编译和度量，不依赖这两页的坐标：

- 自选图形去掉默认 `p:style` 主题阴影，文本框关掉 `spAutoFit`。
- 墨迹盒可以抬成文本框（`box_is_ink`），字号按 1440px = 960pt 换算。
- `home_plate` 在缺少枚举时写成 `homePlate` 预设；`shape_adjust` 控制箭头尖。
- `char_spacing_pt` 写入 run；图片 `mask: circle` 保留圆形透明。
- 中文 OCR 相邻字合并成行；评分增加 blur L1、平移容差边缘 F1、ink IoU、小范围平移 SSIM。优化器一轮可以接受多个改进字段。

## 物理上限

并排已经能读出同一套标题、KPI、四季度、时间轴和三栏，没有碎字墙，没有主题脏阴影，不缺整块。还没有到「盖住一半分不出来」，原因是：

- 原图字体不是 Noto Sans CJK。笔画对不齐时，SSIM 和 1px 边缘 F1 会停在 0.6 附近。诊断里即使几何完全正确，含文字的页在 LibreOffice 下 SSIM 也只有大约 0.80，门禁 0.92 对这种页不成立。
- LibreOffice 的中西文间距和 PowerPoint 不同，字符间距属性在这里不生效，只能把片段拆开摆。
- 插画和三个图标是原图圆形裁剪，不是可编辑矢量。换渲染器抗锯齿会再差一截。
- 没有 PowerPoint，不能给出正式 PASS。
