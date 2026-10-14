# 图片分辨率转换器 (img_resize)

读取图片分辨率并缩放到任意指定尺寸的 Python 小工具。支持三种缩放模式，可打包成单文件 `.exe`，在 Windows 上免安装 Python 直接运行。

## 功能

- 打印原始分辨率
- 缩放到严格 `W × H`
- 三种模式：
  - `stretch` —— 直接拉伸铺满（可能变形）
  - `fit` —— 等比缩放 + 居中留边（不变形，留边可指定颜色）
  - `crop` —— 等比缩放 + 居中裁剪（不变形，无留边）

## 命令行用法

```
python img_resize.py <输入图片> <宽> <高> [--mode 模式] [--out 输出路径] [--bg 填充色]
```

示例：

```bash
# 拉伸到 500x300（默认模式）
python img_resize.py in.jpg 500 300

# 等比缩放 + 白色留边
python img_resize.py in.jpg 500 300 --mode fit

# 等比缩放 + 黑色留边
python img_resize.py in.jpg 500 300 --mode fit --bg 0,0,0

# 等比缩放 + 居中裁剪
python img_resize.py in.jpg 500 300 --mode crop

# 指定输出文件名
python img_resize.py in.jpg 500 300 --mode crop --out result.png
```

参数说明：

| 参数 | 必填 | 说明 |
|------|------|------|
| `输入图片` | 是 | 图片路径，支持 jpg/png/bmp/webp 等 |
| `宽` | 是 | 目标宽度（像素） |
| `高` | 是 | 目标高度（像素） |
| `--mode` | 否 | `stretch`(默认) / `fit` / `crop` |
| `--out` | 否 | 输出路径；不给则自动用 `原名_宽x高.png` |
| `--bg` | 否 | `fit` 留边颜色，如 `255,255,255` 或 `#ffffff`，默认白色 |

## 打包成 .exe（两种方式）

### 方式一：GitHub Actions（无需本地环境，推荐）

1. 把本目录推送到一个 GitHub 仓库（public / private 均可）：
   ```bash
   git init
   git add .
   git commit -m "add img_resize"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```
2. 推送后自动触发构建；也可以到仓库 **Actions** 页面点 **Run workflow**。
3. 构建完成后，在该次运行的 **Artifacts** 里下载 `img_resize-windows`，解压即得 `img_resize.exe`。

### 方式二：本地 Windows 一键打包

1. 装好 Python 3.8+（安装时勾选 *Add python.exe to PATH*）
2. 双击 `build.bat`，等 2–3 分钟
3. 生成的 `dist\img_resize.exe` 即为单文件成品

## exe 用法

与 Python 版完全一致：

```bat
img_resize.exe in.jpg 500 300 --mode fit --out out.png
```

## 依赖

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/)（`pip install pillow`）
- 打包需要 [PyInstaller](https://pypi.org/project/pyinstaller/)（`pip install pyinstaller`）