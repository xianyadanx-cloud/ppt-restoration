# 鱼丸两页视觉还原迭代

金样例是「目标追溯 / 工作目标拆解」两页，规范画布 1440×810。对比一律用 LibreOffice 24.2 渲染后缩放到画布再算项目指标。左图为原图，右图为还原。本机没有 PowerPoint，正式 PASS 不可用，下列数字都是 PREVERIFIED。

用户给出的旧基线是残页：case1 SSIM ≈ 0.635（底部时间轴和后两行被切掉），case2 SSIM ≈ 0.590（接近 OCR 碎字墙）。本轮从完整页面重新做，所以 case1 的 SSIM 不能和那次残页直接比高低，文字墨迹重叠（ink IoU）和并排观感更能说明有没有对齐。第 5 轮之后 SSIM 会贴着字体光栅平台挪动，进步以并排和 ink IoU 一起看。

## 指标

| 轮次 | case1 SSIM | case1 ink IoU | case1 blur L1 | case2 SSIM | case2 ink IoU | case2 blur L1 |
|---|---:|---:|---:|---:|---:|---:|
| 1 初版整页 | 0.453 | 0.385 | 0.066 | 0.525 | 0.362 | 0.079 |
| 2 季度卡片与栏目 | 0.477 | 0.319 | 0.065 | 0.582 | 0.375 | 0.071 |
| 3 按像素墨迹重排 | 0.622 | 0.632 | 0.037 | 0.637 | 0.495 | 0.049 |
| 4 拆开中西文、收箭头 | 0.628 | 0.626 | 0.038 | 0.637 | 0.497 | 0.050 |
| 5 字重与箭头尖 | 0.627 | 0.625 | 0.038 | 0.637 | 0.499 | 0.050 |
| 6 真箭头、渐变轴、台灯入画 | 0.649 | 0.711 | 0.033 | 0.665 | 0.555 | 0.043 |
| 7 轴色与概述条 | 0.657 | 0.713 | 0.032 | 0.670 | 0.553 | 0.042 |
| 8 标题压到 750px | 0.664 | 0.716 | 0.031 | 0.667 | 0.546 | 0.043 |
| 9 圆垫让开正文 | 0.664 | 0.716 | 0.031 | 0.670 | 0.556 | 0.042 |
| 10 圆垫加大、圆点外露 | 0.664 | 0.716 | 0.031 | 0.674 | 0.564 | 0.041 |
| 11 加大飘带字、玻璃层未透明 | 0.644 | 0.724 | 0.033 | 0.660 | 0.552 | 0.044 |
| 12 高光改为半透明 | 0.654 | 0.729 | 0.030 | 0.669 | 0.562 | 0.041 |
| 13 17pt Black、收光晕 | 0.655 | 0.728 | 0.031 | 0.668 | 0.563 | 0.041 |

第 6 轮是几何上最大的一跳：case1 ink IoU 0.625 → 0.711。第 8 到第 10 轮 case1 的 SSIM 停在 0.664、ink IoU 停在 0.716。第 11 轮把飘带标题加大并铺上玻璃层，但高光被画成不透明白条，SSIM 掉到 0.644，ink 仍升到 0.724。第 12 轮修好透明度，case1 ink IoU 到 0.729，是目前最高。第 13 轮的 case1 SSIM 是 0.655，低于第 10 轮的 0.664，因为更大的字和阴影改变了光栅；ink IoU 停在 0.728。case2 在第 11 轮被过厚的图标光晕拖到 0.660 / 0.552，第 13 轮回到 0.668 / 0.563，仍略低于第 10 轮的 0.674 / 0.564。

## 每轮改了什么

1. 去掉主题阴影和自动换行，用闭式字号把两页搭出来。几何是目测的，文字整体错位，差异图是重影。
2. 补上四季度卡片、时间轴和 case2 的三栏。`homePlate` 在 python-pptx 里没有枚举，箭头被静默丢掉。
3. 从原图像素量出标题、正文行、卡片、KPI、时间轴圆点的墨迹盒和色值，按 LibreOffice 实测的上升线偏移摆字。case2 插画和三个图标用原图裁剪，图标加圆形透明蒙版，避免方块把邻栏文字烤进去。
4. LibreOffice 会在汉字和 `/`、数字、`@` 之间插入大约 10px 的空隙，`spc` 对它无效。中西文拆成相邻文本框，空隙回到 3–6px。标题墨迹宽从 792px 收到 759px（原图 748px）。
5. 页眉账号改回加粗，季度箭头尖调浅，飘带文字避开图标。`shape_adjust=0.04` 在 47px 高的飘带上只露出大约 2px 的尖，人眼仍看成扁矩形。
6. 四条季度标题改成真正的 homePlate。原图尖深约 17px，高度 47px，`adj = 17/47 = 0.36`。卡片加上 1.4px 冷灰描边 `#A6B7BF`，圆角从 14px 收到约 8px。时间轴改成一条多段渐变（浅蓝 → 深蓝 → 红），圆点加浅色外环和受控外阴影（模糊 7px、不透明度 0.28），没有把主题 `p:style` 加回去。case2 插画从 x=1024 改到 x=968，台灯和气泡进画。三色条按轮廓加高到 140px，箭头尖 `adj=0.23`。
7. 时间轴去掉过渡处的脏棕色，圆点外环收薄。概述条缩短到台灯之前，填色改成接近原图的极淡暖色。图标放大到 132px 后挡住了飘带正文。
8. 标题墨迹宽收到 750px（原图 748px），整体下移 2px。插画再向下裁一截，把书桌弧线带上。图标缩到 110px 后外圈和圆点都没了，case2 ink IoU 掉到 0.546。
9. 圆垫回到 136px 并向左靠到接缝上，飘带文字改到圆垫右侧。case2 ink IoU 回到 0.556。
10. 圆垫加到 154px，连接圆点画在圆形蒙版外面。case2 SSIM 0.674、ink IoU 0.564。玻璃外圈仍被蒙版切掉一圈。
11. 飘带标题从 13pt Bold 加大。卡片、概述条、KPI 用自上而下的渐变，飘带和 case2 箭头条保持从左到右的渐变。顶部加白色高光条，阴影写进 `outerShdw`（模糊 5–8px、距离 2px、不透明度 0.14–0.28），没有 `p:style`。case2 箭头条加内高光，三个圆图标加外圈光晕。`fill_opacity` 没有写到颜色上，LibreOffice 把高光画成实心白条，概述条顶部被盖白，图标光晕是一圈实心白环。
12. 编译器改为在形状属性里递归找到 `srgbClr` 再写 `a:alpha`。高光变成半透明之后，case1 ink IoU 0.729、blur L1 0.030，case2 回到 0.669 / 0.562。
13. 原图 Q1 飘带白字占 y348–369，大约 22px 高、200px 宽。13pt Bold 盖不住这一块。改成 17pt，字体名用 Noto Sans CJK SC Black，不再叠加 bold，避免 LibreOffice 再加粗一档。渲染白字占 y345–368，行里的白像素比原图多，高度对齐，笔画更满。KPI 去掉白色顶条，渐变改为 `#C5DCF4 → #B3D0EE → #C9E0F4`。图标光晕收到外扩 3px、填充不透明度 0.10、描边 1.6px、glow 半径 3px。底部药丸高 30px、圆角 14px，字框上移 2px，填色按远离文字处的采样改成 `#D5E9F8` / `#F8E3DF`。第 13 轮成品里白色填充带 alpha 的节点有 5 处，`outerShdw` 32 处，`effectRef` 为 0。

对比图：

- [第 1 轮 case1](docs/iteration/round1_case1.png) / [case2](docs/iteration/round1_case2.png)
- [第 2 轮 case1](docs/iteration/round2_case1.png) / [case2](docs/iteration/round2_case2.png)
- [第 3 轮 case1](docs/iteration/round3_case1.png) / [case2](docs/iteration/round3_case2.png)
- [第 4 轮 case1](docs/iteration/round4_case1.png) / [case2](docs/iteration/round4_case2.png)
- [第 5 轮 case1](docs/iteration/round5_case1.png) / [case2](docs/iteration/round5_case2.png)
- [第 6 轮 case1](docs/iteration/round6_case1.png) / [case2](docs/iteration/round6_case2.png)
- [第 7 轮 case1](docs/iteration/round7_case1.png) / [case2](docs/iteration/round7_case2.png)
- [第 8 轮 case1](docs/iteration/round8_case1.png) / [case2](docs/iteration/round8_case2.png)
- [第 9 轮 case1](docs/iteration/round9_case1.png) / [case2](docs/iteration/round9_case2.png)
- [第 10 轮 case1](docs/iteration/round10_case1.png) / [case2](docs/iteration/round10_case2.png)
- [第 11 轮 case1](docs/iteration/round11_case1.png) / [case2](docs/iteration/round11_case2.png)
- [第 12 轮 case1](docs/iteration/round12_case1.png) / [case2](docs/iteration/round12_case2.png)
- [第 13 轮 case1](docs/iteration/round13_case1.png) / [case2](docs/iteration/round13_case2.png)

## 字体

按字形宽度和墨迹扫过本机中文字体：Noto Sans CJK SC 的 Regular / Medium / DemiLight / Bold，Noto Serif CJK SC Bold，文泉驿微米黑，Droid Sans Fallback。标题「核心工作回顾」的目标是跨度 266px、墨迹高 45px。

Noto Sans CJK SC Bold 30pt 的 LibreOffice 渲染跨度是 266px、高 42px，是这批里最接近的。Medium 30pt 跨度 265px、高 42px，笔画更轻。文泉驿和 Droid 在 LibreOffice 里会拆碎或回退到别的字，宋体更窄更矮。系统里没有苹方、独立安装的思源黑体或阿里巴巴普惠体。标题因此用 Noto Sans CJK SC Bold，正文用同一家族的 Regular。这是这次测量的结果。

汉字前进量按 1em 摆，西文片段单独成框。30pt 标题的整行墨迹从第 4 轮的 759px 收到第 8 轮的 750px，原图是 748px。

Q1–Q4 飘带标题单独用 Noto Sans CJK SC Black 17pt，不叠加 bold。同一家族的 Bold 13pt 明显矮于原图大约 22px 的白字。`fc-match` 把这个家族名解析到 NotoSansCJK-Black.ttc 的 Black 样式。

## 代码侧能力

这些改动进了编译和度量，不依赖这两页的坐标：

- 自选图形去掉默认 `p:style` 主题阴影，文本框关掉 `spAutoFit`。显式 `style.shadow` 仍写成 `outerShdw`。
- 墨迹盒可以抬成文本框（`box_is_ink`），字号按 1440px = 960pt 换算。
- `home_plate` 在缺少枚举时写成 `homePlate` 预设；`shape_adjust` 控制箭头尖。python-pptx 的 `PENTAGON` 预设本身就是 `homePlate`。
- `char_spacing_pt` 写入 run；图片 `mask: circle` 保留圆形透明。
- 中文 OCR 相邻字合并成行；评分增加 blur L1、平移容差边缘 F1、ink IoU、小范围平移 SSIM。优化器一轮可以接受多个改进字段。
- `fill_opacity` 写到 `solidFill` 里的 `srgbClr` 上。`Element.find` 不递归，以前嵌套的颜色节点到不了，透明度被编译成不透明色。

## 物理上限

并排已经能读出同一套标题、KPI、四季度箭头、时间轴和三栏。没有碎字墙，没有主题脏阴影，不缺整块。还没有到「盖住一半分不出来」。下面把还能改的和改不动的分开。

第 11 轮的实心白条不是渲染器上限。形状透明度没有写进颜色，LibreOffice 只能画不透明填充。第 12 轮修好之后，第 13 轮的 PPTX 里白色 `srgbClr` 带着 `a:alpha`，测试锁定 `<a:alpha val="30000"/>`。

飘带字号也不是上限。原图 Q1 白字行是 y348–369。第 13 轮渲染是 y345–368，高度对齐，行内白像素更多。再加大一号会超出大约 200px 的墨迹宽。剩下的差别是 Noto Black 的笔画形状和抗锯齿，原图那套黑体不在本机字体里。页眉标题仍是 Bold 30pt，墨迹高 42px，原图 45px。

KPI 和概述条的色差已经收到几个 RGB 点里。采样点 (500, 180)：原图 (231, 235, 244)，第 13 轮 (227, 240, 248)。KPI 顶部 (950, 155)：原图 (191, 217, 244)，第 13 轮 (182, 210, 239)，比第 12 轮那层洗白的顶条更接近，而且略深。再压暗会离开这些采样。LibreOffice 的线性渐变没有原图那层更软的玻璃颗粒。

下面这些是渲染器或字体的上限，并排里还能看见：

- 原图黑体不是 Noto。页眉笔画对不齐。诊断里几何完全正确的含文字页，在 LibreOffice 下 SSIM 也只有大约 0.80，门禁 0.92 对这种页不成立。case1 SSIM 从第 10 轮的 0.664 落到第 13 轮的 0.655，是更大的字和阴影改了光栅；这项改动的读数是 ink IoU 0.716 → 0.728。
- LibreOffice 忽略 run 的 `spc`，汉字和 `/`、数字之间的空隙只能靠拆框。标题还宽 2px，斜线两侧仍比原图略松。
- 时间轴圆点的高光是径向的。现在用两层圆加轻微外阴影近似，阴影写在 `effectLst` 里，不是主题脏阴影。
- case2 图标的玻璃外圈和细连接茎是软光栅。圆形蒙版再加大就会把箭头角裁进来（第 7 轮和第 11 轮），再缩小就丢掉外圈（第 8 轮）。DrawingML 的 glow 各向同性，做不出原图那圈镜面高光加细茎。连接圆点是原生圆形，没有那条细茎。第 11 轮把光晕加厚后，case2 ink IoU 掉到 0.552；第 13 轮收薄后回到 0.563，和第 10 轮的 0.564 同一水平。
- 插画和三个图标仍是原图裁剪，不是可编辑矢量。台灯和气泡已经在裁切框内。
- 没有 PowerPoint，不能给出正式 PASS。

---

# Gemini 主机迭代（gemini-host-fixes）

从第 14 轮起改由 Gemini 3.8 Flash High 作为 Pass 1/Pass 2 主机，在产品侧修契约与编译器，再让主机重跑两页。金样例仍是同一套 `ppt-sample/case{1,2}/canonical.png`（1440×810），指标用 LibreOffice 渲染后与金样对齐的 SSIM / ink IoU / edge F1，综合分 = mean(ssim, ink_iou, edge_f1)。

对照基线：

| 来源 | case1 ssim/ink/edge (score) | case2 ssim/ink/edge (score) |
|---|---|---|
| Gemini 一次性（修契约前） | 0.712 / 0.555 / 0.315 (0.527) | 0.726 / 0.494 / 0.335 (0.518) |
| 旧第 13 轮自报（相对其自家金样） | 0.655 / 0.728 / — | 0.668 / 0.563 / — |
| 旧第 13 轮渲染 vs **本仓库金样** | 0.405 / 0.176 / 0.132 | 0.546 / 0.272 / 0.201 |

旧第 13 轮的金样与本仓库 `ppt-sample` 金样不一致（旧金 vs 本金：c1≈0.366、c2≈0.529），所以旧表数字不能和本轮直接比；下面表一律相对本仓库金样。

评测闸门是 **EVAL-ONLY**：`run_case.sh` 在 block-init 后自动把全部 block 标成 APPROVED，跳过人工审阅，只为度量主机+产品闭环。正式流水线仍要人审。

## Gemini 轮次指标

| 轮次 | 产品增量 | case1 ssim | case1 ink | case1 edge | case1 score | case2 ssim | case2 ink | case2 edge | case2 score |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G1 | wrap 默认 / z_index 排序 / OCR TSV / audit content + CI | 0.703 | 0.568 | 0.323 | 0.531 | 0.693 | 0.506 | 0.328 | 0.509 |
| G2 | + `pptrestore preview` 自检环 | 0.698 | **0.645** | 0.356 | **0.566** | 0.715 | 0.601 | 0.375 | 0.563 |
| G3 | + text_fidelity 契约 + tesseract OCR（严格冲突） | 0.722 | 0.618 | 0.339 | 0.560 | **0.748** | **0.658** | **0.393** | **0.600** |
| G4 | + text_size_hints + 渐变 stops 容错（dict / 色在前） | 0.700 | 0.590 | 0.362 | 0.551 | 0.719 | 0.641 | 0.373 | 0.578 |
| G5 | + OCR 模糊同意 + runs≡text + CJK/Latin 空格闸 + 可编辑透明度 | （跑） | | | | | | | |

当前 best：case1 = G2（ink 0.645），case2 = G3（score 0.600）。

## 每轮改了什么（Gemini）

1. **G1**：修四处死结（body 默认 wrap、按 id 的 z_index 排序、OCR TSV 引号、audit `content` 契约）和 Python 3.12 / Pillow 13 CI。主机一次性出稿；case1 审计首通 VALIDATED；case2 渐变写成 `{color, position}` 对象，编译器按 `s[0]` 取值整段丢掉（build rc=1）。
2. **G2**：新产品命令 `pptrestore preview`（LibreOffice 渲染 → side_by_side / diff / worst regions，不写 case 状态）。Pass 1 提示强制自检约 3 轮。case1 ink 0.568→0.645，case2 ink 0.506→0.601。仍见：CJK/拉丁空格、字号偏大/偏小、渐变与玻璃层扁平。
3. **G3**：`text_fidelity_contract` + 本机装上 tesseract chi_sim（`--ocr auto`）。OCR 冲突规则仍是严格包含，tesseract 噪声触发大量假冲突，repair 轮可能把 runs 改成 OCR 乱码（case1 `node-card3-sub` runs=`01. 内`+`容价值深化`，DOM 校验失败 build rc=1）。跑中途 preview 已带上后加的 `text_size_hints`（可编辑安装）。case2 综合分升到 0.600，成为当前 best。
4. **G4**：preview 增加按墨迹带测的 `text_size_hints`（字形高比、建议 pt、行数、位移）；编译器 `normalize_gradient_stops` 接受 dict / 色在前。两案均出 PPTX；分数未超过 G2/G3。
5. **G5**（进行中）：ingest 对 OCR 用折叠+数字钉死+窗口 ratio≥0.75 的模糊同意；`payload.runs` 必须拼出 `payload.text`；CJK↔拉丁/数字/`@` 间空格需 `verbatim_spaces` 才能过；编译器支持 `#RRGGBBAA` / `rgba()` / 渐变 stop `opacity`（LibreOffice 实测可透）。

## 诚实上限（相对 100% 还原）

- 原图黑体不在本机，Noto 笔画形状不同；含文字页 LibreOffice 下几何正确时 SSIM 也大约止于 0.80 一带。
- LibreOffice 忽略 run `spc`；中西文空隙只能拆框或接受空格闸的取舍。
- 图标玻璃外圈、细连接茎、径向高光是软光栅；DrawingML glow 各向同性做不出来，圆形蒙版裁切有权衡。
- 插画仍是原图裁剪，不是可编辑矢量。
- 主机有方差：同一提示连续两轮分数可差几个点；修产品后要多跑才能判断平台。
