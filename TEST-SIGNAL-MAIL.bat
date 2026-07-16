@echo off
chcp 65001 >nul
title Trading Assistant AI - Test Signal Mail (lenh cho)
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo Dang gui MAIL TIN HIEU MAU (lenh cho / limit) toi hop thu cua ban...
"%PY%" send_test_signal.py
echo.
pause
