# PPT Restoration 开发者与贡献指南

欢迎参与 PPT 智能还原工作空间的开发与贡献！

---

## 🛠️ 1. 本地开发环境准备

### 环境要求
* Python 3.9+
* macOS / Linux / Windows
* LibreOffice（用于无头 PPTX 转 PDF 与图片渲染比对，可选但推荐）

### 安装步骤
```bash
# 1. 克隆代码仓库
git clone <repository_url>
cd workspace

# 2. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

---

## 🧪 2. 运行单元测试与回归套件

在提交任何代码或修改引擎前，请确保所有测试用例均通过：

```bash
# 运行全部单元测试
.venv/bin/python -m unittest tests/test_workspace.py
```

---

## 🎨 3. 新建幻灯片还原工作流

1. **准备素材**：将原图或截图放入 `input/` 目录（例如 `input/slide_demo.png`）。
2. **初始化脚手架**：
   ```bash
   .venv/bin/python tools/init_deck.py input/slide_demo.png
   ```
3. **编写与调试代码**：在 `slides/build_slide_demo.py` 中按 Block 编写模块化渲染函数，并利用 `--cumulative-up-to` 渐进式验证：
   ```bash
   .venv/bin/python slides/build_slide_demo.py --cumulative-up-to 1
   ```
4. **DOM 质量检查**：
   ```bash
   .venv/bin/python tools/inspect_pptx.py output/slide_demo.pptx
   ```
5. **生成 Visual Diff 对比图**：
   ```bash
   .venv/bin/python tools/render_and_diff.py output/slide_demo.pptx input/slide_demo.png -o output/diff_demo.png
   ```

---

## 📦 4. Git 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

* `feat(builder)`: 新增 SlideBuilder 组件或渲染能力
* `feat(cases)`: 完成新的幻灯片高保真还原案例
* `fix(tools)`: 修复工具链或坐标换算缺陷
* `docs`: 文档、规范或 API 参考更新
* `test`: 单元测试与回归套件补充
