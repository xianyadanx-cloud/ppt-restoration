# Image to PowerPoint

将图片或 PDF 页面还原为可编辑的 PowerPoint，提供标准化、SceneSpec v2 校验、原生编译、逐块审核和内容对账。

**这是供多模态 Agent 使用的本地工具。** 图片识别由你使用的 Agent 完成；Python 程序不内置模型、不调用模型 API、不包含密钥。单独运行命令不会自动识别整张图片并完成还原。

## 安装

从 GitHub 下载 ZIP 并解压，或克隆仓库，进入包含本文件的目录：

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 使用：.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
pptrestore doctor
```

需要 Python 3.9+。核心依赖 Pillow、python-pptx、pypdf 自动安装。开发时使用 `python -m pip install -e ".[dev]"`。

可选增强（在源码目录执行）：

```bash
python -m pip install ".[font-strict]"
python -m pip install ".[ocr]"
python -m pip install ".[powerpoint-windows]"
```

这些命令安装 Python 包，不安装 Office、系统字体、Tesseract 或 Poppler。

## 系统依赖

| 功能 | 外部要求 |
| --- | --- |
| 图片标准化、校验、生成 PPTX | 仅核心 Python 依赖 |
| PDF 输入 | Poppler 的 pdftoppm 在 PATH 中 |
| 真实渲染和审核 | PowerPoint 或 LibreOffice，以及 PDF 栅格化工具 |
| WPS 预验 | 支持转换的 WPS CLI，或从 WPS 手动导出的 PDF |
| 中文显示 | 安装包含所需中文字符的字体 |
| macOS OCR | Swift 和可用的 Apple Vision SDK，适配脚本随包安装 |
| Tesseract OCR | 系统 tesseract 和 chi_sim、eng 等所需语言包 |

macOS 可用 Homebrew 安装 poppler 和 libreoffice，Ubuntu/Debian 可安装 poppler-utils、libreoffice-impress、fonts-noto-cjk。Windows 安装 Office 或 LibreOffice，并将 Poppler 的 bin 目录加入 PATH。运行 `pptrestore doctor` 检查本机能力。

没有渲染器仍能生成 PPTX，但无法完成真实渲染审核。LibreOffice/WPS 的最高结论是 PREVERIFIED；正式 PASS 需要 PowerPoint 渲染及所有门禁通过。OCR 失败或识别为空不意味着图片没有文字。

## 使用

让能读取图片和执行本地命令的 Agent 阅读 [SKILL.md](SKILL.md)，并遵守 [AGENTS.md](AGENTS.md)。

1. 准备案例。输入输出目录可自行指定：

```bash
pptrestore prepare /path/to/slide.png --case-dir /path/to/my-case --ocr auto
# PDF 用 --page-index 0 选择第 1 页
```

2. Agent 读取案例中的 canonical.png、evidence.json、agent_request.json 和导出的提示模板。第一遍生成 scene.proposed.json，第二遍重新看图生成 content_audit.proposed.json。

3. 校验并生成蓝图：

```bash
pptrestore ingest /path/to/my-case /path/to/my-case/scene.proposed.json --content-audit /path/to/my-case/content_audit.proposed.json
pptrestore blueprint /path/to/my-case
```

NEEDS_REVIEW 必须修正后重新 ingest。blueprint 返回分块图和 blueprint.json 的实际路径。用户确认后：

```bash
pptrestore block-init /path/to/my-case /path/from/blueprint/blueprint.json
pptrestore next /path/to/my-case
```

4. 按 next 返回的参数构建当前块并审核。block_1 替换成实际 Block ID：

```bash
pptrestore build /path/to/my-case --blocks block_1 --output /path/to/my-case/block_1.pptx
pptrestore review /path/to/my-case --block block_1 --renderer auto
```

展示局部对比和累计预览，用户明确确认后，使用 review 返回的实际报告路径：

```bash
pptrestore block-approve /path/to/my-case block_1 --review-report /path/from/review/review.json --user-confirmed
pptrestore next /path/to/my-case
```

后续块按 next 返回的累计范围构建。全部通过后：

```bash
pptrestore build /path/to/my-case --output /path/to/result.pptx
pptrestore verify /path/to/my-case /path/to/result.pptx --renderer auto
```

默认 hybrid_editable 保持业务内容原生，允许复杂装饰使用图片。全页禁止图片时，build 增加 `--render-strategy strict_native`。WPS 导出 PDF 可用 `--renderer wps --wps-pdf /path/to/exported.pdf` 导入。

每条命令支持 --help。修订、优化和文件协议见 [PIPELINE.md](docs/PIPELINE.md)。

## 项目结构

- src/ppt_restore：核心代码、CLI、随包安装的 prompt 和 OCR 资源
- tests：使用临时目录的自动化测试
- docs：架构、协议和开发说明
- AGENTS.md、SKILL.md：还原约束和 Agent 入口
- pyproject.toml：唯一依赖与打包配置

仅支持 SceneSpec v2。运行产物归案例目录所有，不属于源代码仓库。内容对账证明已提交场景内容在 PPT 中未丢失，不能证明原图识别正确；视觉质量仍需人工审核。
