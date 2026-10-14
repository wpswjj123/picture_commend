# 图片分辨率转换器 (img_resize)

读取图片分辨率并缩放到任意指定尺寸的小工具。支持三种缩放模式，可打包成单文件 `.exe`，在 Windows 上免安装 Python 直接运行。

提供 **两个版本**：

| 版本 | 文件 | 说明 |
|------|------|------|
| **图形界面版（推荐）** | `img_resize_gui.py` → `img_resize_gui.exe` | 双击打开窗口，所有操作都在界面里点选，无需命令行 |
| 命令行版 | `img_resize.py` → `img_resize.exe` | 适合脚本 / 批量自动化 |

---

## 图形界面版（img_resize_gui）

双击 `img_resize_gui.exe`，界面里可以：

- **选择图片**：单张 / 多张 / 整个文件夹（自动递归收集）
- **预览**：左侧「原图」、右侧「效果预览」，实时看缩放结果
- **目标尺寸**：填宽 × 高
- **缩放模式**：直接拉伸 / 等比留边 / 等比裁剪
- **留边颜色**：调色板取色（仅「等比留边」模式生效）
- **输出目录**：与源文件同目录，或自定义
- **文件名后缀 / 输出格式**（PNG / JPG / 原格式）
- **开始转换**：带进度条与日志，支持批量

---

## 命令行版（img_resize）

```
python img_resize.py <输入图片> <宽> <高> [--mode 模式] [--out 输出路径] [--bg 填充色]
```

示例：

```bash
python img_resize.py in.jpg 500 300                    # 拉伸（默认）
python img_resize.py in.jpg 500 300 --mode fit         # 等比留边
python img_resize.py in.jpg 500 300 --mode fit --bg 0,0,0   # 黑色留边
python img_resize.py in.jpg 500 300 --mode crop        # 等比裁剪
python img_resize.py in.jpg 500 300 --mode crop --out result.png
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `输入图片` | 是 | 图片路径 |
| `宽` / `高` | 是 | 目标尺寸（像素） |
| `--mode` | 否 | `stretch`(默认) / `fit` / `crop` |
| `--out` | 否 | 输出路径；不给则自动用 `原名_宽x高.png` |
| `--bg` | 否 | `fit` 留边颜色，如 `255,255,255` 或 `#ffffff` |

三种模式区别：

- `stretch` —— 直接拉伸铺满，可能变形
- `fit` —— 等比缩放 + 居中留边，不变形
- `crop` —— 等比缩放 + 居中裁剪，不变形、无留边

---

## 打包成 .exe（两种方式）

### 方式一：GitHub Actions（无需本地环境，推荐）

1. 推送到 GitHub 仓库：
   ```bash
   git init && git add . && git commit -m "add img_resize"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```
2. 自动触发构建；也可到 **Actions** 页点 **Run workflow**。
3. 构建完成后，在 **Artifacts → img_resize-windows** 下载，包含两个 exe。

### 方式二：本地 Windows 一键打包

1. 装好 Python 3.8+（勾选 *Add python.exe to PATH*）
2. 双击 `build.bat`，等几分钟
3. 产物在 `dist\`：`img_resize_gui.exe`（界面版）、`img_resize.exe`（命令行版）

---

## 依赖

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/)（`pip install pillow`）
- 打包需要 [PyInstaller](https://pypi.org/project/pyinstaller/)（`pip install pyinstaller`）
- 图形界面用 Python 自带的 tkinter（Windows 版 Python 默认自带）