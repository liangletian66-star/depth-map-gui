@echo off
chcp 65001 >nul
REM ============================================================
REM  打包「视频深度图工具」为单文件 exe（仅 Windows）
REM  产物：dist\视频深度图工具.exe
REM  依赖同目录的 venv（exe 会调用它来跑推理）
REM ============================================================

cd /d "%~dp0\.."

echo [1/2] 安装打包工具 PyInstaller...
venv\Scripts\pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [2/2] 开始打包...
venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed ^
  --name "视频深度图工具" ^
  --icon "assets\icon.ico" ^
  --distpath "." ^
  --workpath "build" ^
  --specpath "build" ^
  src\depth_gui.py

echo.
echo 完成！exe 已生成在项目根目录。
pause
