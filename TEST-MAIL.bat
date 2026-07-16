@echo off
chcp 65001 >nul
title Trading Assistant AI - Test Mail
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo Dang gui mail test qua tat ca kenh dang bat...
"%PY%" run_monitor.py --test
echo.
pause
