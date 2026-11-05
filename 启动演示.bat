@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0app"
set PYTHONUTF8=1
where py >nul 2>nul
if %errorlevel%==0 (
    py server.py --port 8848
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python server.py --port 8848
    goto :end
)
echo 未找到 Python，请先安装 Python 3.9 或更高版本，然后重新运行本文件。
pause
:end
endlocal
