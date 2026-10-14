@echo off
REM ============================================================
REM  build.bat  —— 在 Windows 上本地一键打包 img_resize.exe
REM  双击运行即可。需要已安装 Python 3.8+ 并勾选 Add to PATH
REM ============================================================
setlocal

echo.
echo ========== 1/3 检查 Python ==========
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装：https://www.python.org/downloads/
    echo        安装时务必勾选 "Add python.exe to PATH"
    pause
    exit /b 1
)
python --version

echo.
echo ========== 2/3 安装依赖 (Pillow + PyInstaller) ==========
python -m pip install --upgrade pip
python -m pip install pillow pyinstaller
if errorlevel 1 (
    echo [错误] 依赖安装失败，检查网络或换用国内镜像：
    echo   python -m pip install pillow pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    pause
    exit /b 1
)

echo.
echo ========== 3/3 打包单文件 exe ==========
python -m PyInstaller --onefile --noconfirm --clean --name img_resize img_resize.py
if errorlevel 1 (
    echo [错误] 打包失败。
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  完成！可执行文件在：  dist\img_resize.exe
echo.
echo  用法示例：
echo    img_resize.exe input.jpg 500 300
echo    img_resize.exe input.jpg 500 300 --mode fit  --out out.png
echo    img_resize.exe input.jpg 500 300 --mode crop
echo ============================================================
pause