# PPT Restoration Workspace (高保真 PPT 智能还原工作空间)

> **基于 SDD（规范驱动开发）与 4 门禁 SOP 的 AI Coding Agent 演示文稿高保真还原系统**

本项目提供了一套面向 AI Coding Agent（如 Claude Code, Cursor, Aider, Antigravity）的工程化 PPT 还原基础设施。将图片/PDF 转化为 **100% 原生可二次编辑、兼具 3D 拟态质感与数据可视化** 的 PowerPoint（`.pptx`）文件。

---

## 🗂️ 核心目录架构与职责划分

工作空间对 **“Agent 体系”**、**“开发规范体系”** 与 **“工程文档”** 进行了明确解耦与分层组织：

```
workspace/
├── agent/                       # 🤖 Agent 体系 (Prompt 库、Skill 契约与操作 SOP)
│   ├── AGENTS.md                # Agent 标准操作流程 (4 大质量门禁、0-1000 坐标系)
│   ├── SKILL.md                 # Agent Skill 契约规范与触发指令
│   └── prompts/                 # SDD 阶段流转的标准 Agent Prompt 模板
│       ├── 01_draft_spec.md
│       ├── 02_draft_plan_eval.md
│       ├── 03_draft_tasks.md
│       ├── 04_execute_tasks.md
│       └── 05_synthesize_learnings.md
│
├── docs/                        # 📚 人类与 Agent 共享的技术参考
│   ├── ARCHITECTURE.md          # 整体系统架构与 Multi-Agent 演进设计
│   ├── API_REFERENCE.md         # SlideBuilder 引擎与 tools 工具链完整 API
│   └── CONTRIBUTING.md          # 本地运行、单测与添加新案例指南
│
├── specs/                       # 📋 开发规范体系 (SDD 规范驱动开发体系)
│   ├── SDD_GUIDE.md             # SDD 工作流与评审门禁指南
│   ├── templates/               # 五大规范模板库
│   │   ├── spec.template.md     # 需求理解与消歧模板
│   │   ├── plan.template.md     # 技术架构与不改清单模板
│   │   ├── tasks.template.md    # 任务拆解与 verify 命令模板
│   │   ├── eval.template.md     # 评测矩阵与验收模板
│   │   └── learnings.template.md# 经验沉淀与复盘模板
│   └── current/                 # 当前还原任务的 SDD 交付归档
│       ├── spec.md              # 需求规格说明书 (US-01~US-05)
│       ├── plan.md              # 4层分层架构与不改清单
│       ├── tasks.md             # 确定性任务执行链
│       ├── eval.md              # 验收评测矩阵 (【通过】)
│       └── learnings.md         # 认知沉淀与工程经验 (L-01~L-04)
│
├── tools/                       # 🛠️ Agent 工具箱与排版引擎
│   ├── pptx_helper.py           # 核心 SlideBuilder 引擎 (0-1000坐标, 进度条, KPI卡, 渐变色)
│   ├── icon_fetcher.py          # 在线矢量图标库检索与主题色注入
│   ├── slice.py                 # 0-1000 归一化局部高精度切片工具
│   ├── render_and_diff.py       # 4级渲染回退自检与双图视觉比对器
│   ├── inspect_pptx.py          # PPTX DOM 树结构深度检查器
│   ├── merge.py                 # 多单页 PPTX 合并工具
│   ├── extract_pdf.py           # PDF 页面拆分工具
│   └── init_deck.py             # 幻灯片构建脚手架生成器
│
├── slides/                      # 🎨 幻灯片构建代码 (业务实现)
│   ├── build_slide_01.py        # Slide 1 (3D 折页书本 + 6 组对比卡片)
│   └── build_slide_02.py        # Slide 2 (原生表格 + 5 组发光胶囊进度条 + 2+1 渐变行动卡)
│
├── input/                       # 📥 原始输入素材 (截图、海报、PDF)
├── assets/                      # 🖼️ 提取的高精无字底图与矢量图标资产
├── output/                      # 📤 交付的 PPTX 文档与合并成果
├── tests/                       # 🧪 自动化单元测试与回归套件
├── AGENTS.md                    # (根目录镜像，保证 Agent 规则加载)
├── SKILL.md                     # (根目录镜像)
├── .gitignore                   # Git 忽略配置
└── requirements.txt             # Python 依赖清单
```

---

## ⚡ 快速开始与使用指南

### 1. 还原一张新的 PPT 图片
```bash
# 1. 将图片放入 input/ 目录 (如 input/slide_demo.png)
# 2. 运行脚手架生成构建脚本
.venv/bin/python tools/init_deck.py input/slide_demo.png

# 3. 编写/运行构建脚本 (支持累加构建调试)
.venv/bin/python slides/build_slide_demo.py --cumulative-up-to 1

# 4. DOM 结构深度检查 (PICTURE=0 严格校验)
.venv/bin/python tools/inspect_pptx.py output/slide_demo.pptx

# 5. 渲染视觉比对图
.venv/bin/python tools/render_and_diff.py output/slide_demo.pptx input/slide_demo.png -o output/diff_demo.png
```

### 2. 运行自动化测试套件
```bash
.venv/bin/python -m unittest tests/test_workspace.py
```

### 3. 多页合并
```bash
.venv/bin/python tools/merge.py output/slide_01.pptx output/slide_02.pptx -o output/final_deck.pptx
```

---

## 📖 技术文档与参考导航

* [**SOP 标准操作规程**](agent/AGENTS.md)
* [**SlideBuilder API 与工具箱参考手册**](docs/API_REFERENCE.md)
* [**系统架构与 Multi-Agent 设计**](docs/ARCHITECTURE.md)
* [**开发者与贡献指南**](docs/CONTRIBUTING.md)
